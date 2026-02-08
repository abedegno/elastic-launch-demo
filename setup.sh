#!/usr/bin/env bash
# ============================================================================
# NOVA-7 Setup & Deploy Script
# ============================================================================
# Validates environment, builds containers, and configures Elastic.
# Usage:
#   ./setup.sh              # Full setup and deploy
#   ./setup.sh --dry-run    # Validate only, do not deploy
# ============================================================================

set -euo pipefail

# ── Color helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
header()  { echo -e "\n${CYAN}══════════════════════════════════════════════════════════${NC}"; echo -e "${CYAN}  $*${NC}"; echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}\n"; }

# ── Parse arguments ──────────────────────────────────────────────────────────
DRY_RUN=false
SKIP_BUILD=false
SKIP_ELASTIC=false

for arg in "$@"; do
    case "$arg" in
        --dry-run)     DRY_RUN=true ;;
        --skip-build)  SKIP_BUILD=true ;;
        --skip-elastic) SKIP_ELASTIC=true ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run       Validate configuration without deploying"
            echo "  --skip-build    Skip Docker image build"
            echo "  --skip-elastic  Skip Elastic configuration check"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# ── Navigate to project root ────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

header "NOVA-7 Launch Demo — Setup & Deploy"

if $DRY_RUN; then
    warn "DRY RUN MODE — will validate only, no changes will be made"
    echo ""
fi

# ── Step 1: Check prerequisites ─────────────────────────────────────────────
header "Step 1: Checking prerequisites"

MISSING_TOOLS=()

if command -v docker &> /dev/null; then
    success "docker found: $(docker --version)"
else
    MISSING_TOOLS+=("docker")
    error "docker not found"
fi

if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    success "docker-compose found"
else
    MISSING_TOOLS+=("docker-compose")
    error "docker-compose not found"
fi

if command -v curl &> /dev/null; then
    success "curl found"
else
    MISSING_TOOLS+=("curl")
    error "curl not found"
fi

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    error "Missing required tools: ${MISSING_TOOLS[*]}"
    error "Please install them before continuing."
    exit 1
fi

# ── Step 2: Load environment variables ───────────────────────────────────────
header "Step 2: Loading environment variables"

if [ -f .env ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    success "Loaded .env file"
else
    warn ".env file not found — using current environment variables"
    if [ -f .env.example ]; then
        info "Hint: copy .env.example to .env and fill in your values"
    fi
fi

# ── Step 3: Validate required environment variables ──────────────────────────
header "Step 3: Validating environment variables"

ERRORS=0
WARNINGS=0

validate_required() {
    local var_name="$1"
    local var_value="${!var_name:-}"
    local description="$2"
    if [ -z "$var_value" ]; then
        error "$var_name is not set — $description"
        ERRORS=$((ERRORS + 1))
    else
        success "$var_name is set"
    fi
}

validate_optional() {
    local var_name="$1"
    local var_value="${!var_name:-}"
    local description="$2"
    if [ -z "$var_value" ]; then
        warn "$var_name is not set — $description (optional)"
        WARNINGS=$((WARNINGS + 1))
    else
        success "$var_name is set"
    fi
}

# Required for Elastic telemetry pipeline
validate_required "ELASTIC_ENDPOINT"  "Elasticsearch endpoint for OTel collector"
validate_required "ELASTIC_API_KEY"   "API key for Elasticsearch"

# Required for OTLP (have defaults but should be validated)
info "OTLP_ENDPOINT=${OTLP_ENDPOINT:-http://otel-collector:4318} (default is fine for Docker)"

# Optional — Twilio notifications
validate_optional "TWILIO_ACCOUNT_SID"  "Required for SMS/voice alerts"
validate_optional "TWILIO_AUTH_TOKEN"   "Required for SMS/voice alerts"
validate_optional "TWILIO_FROM_NUMBER"  "Twilio sender phone number"
validate_optional "TWILIO_TO_NUMBER"    "Alert recipient phone number"

# Optional — Slack notifications
validate_optional "SLACK_WEBHOOK_URL"   "Required for Slack alerts"

echo ""
if [ $ERRORS -gt 0 ]; then
    error "$ERRORS required variable(s) missing"
    if $DRY_RUN; then
        error "Dry run validation FAILED"
        exit 1
    else
        error "Cannot proceed with deployment. Please set the required variables."
        exit 1
    fi
fi

if [ $WARNINGS -gt 0 ]; then
    warn "$WARNINGS optional variable(s) missing — some features will be disabled"
fi

# ── Step 4: Validate project structure ───────────────────────────────────────
header "Step 4: Validating project structure"

REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile"
    "requirements.txt"
    "otel-collector-config.yaml"
    "app/main.py"
    "app/config.py"
    "app/telemetry.py"
    "app/chaos/controller.py"
    "app/chaos/channels.py"
    "app/services/manager.py"
    "app/dashboard/static/index.html"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$f" ]; then
        success "$f"
    else
        error "Missing: $f"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -gt 0 ]; then
    error "Project structure validation failed"
    exit 1
fi

success "Project structure is valid"

# ── Step 5: Test Elastic connectivity ────────────────────────────────────────
if ! $SKIP_ELASTIC; then
    header "Step 5: Testing Elastic connectivity"

    ELASTIC_ENDPOINT="${ELASTIC_ENDPOINT:-}"
    ELASTIC_API_KEY="${ELASTIC_API_KEY:-}"

    if [ -n "$ELASTIC_ENDPOINT" ] && [ -n "$ELASTIC_API_KEY" ]; then
        if $DRY_RUN; then
            info "Would test connectivity to: $ELASTIC_ENDPOINT"
        else
            info "Testing connection to $ELASTIC_ENDPOINT ..."
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: ApiKey $ELASTIC_API_KEY" \
                "$ELASTIC_ENDPOINT" \
                --connect-timeout 10 \
                2>/dev/null || echo "000")

            if [ "$HTTP_CODE" = "200" ]; then
                success "Elastic cluster is reachable (HTTP $HTTP_CODE)"
            elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
                error "Elastic returned HTTP $HTTP_CODE — check your API key"
                exit 1
            elif [ "$HTTP_CODE" = "000" ]; then
                warn "Could not reach $ELASTIC_ENDPOINT — check the URL (may work from within Docker network)"
            else
                warn "Elastic returned HTTP $HTTP_CODE — may still work from Docker"
            fi
        fi
    else
        warn "Skipping Elastic connectivity test (credentials not set)"
    fi
else
    info "Skipping Elastic connectivity test (--skip-elastic)"
fi

# ── Step 6: Build Docker images ──────────────────────────────────────────────
if ! $SKIP_BUILD; then
    header "Step 6: Building Docker images"

    if $DRY_RUN; then
        info "Would run: docker compose build"
    else
        info "Building NOVA-7 container image..."
        if docker compose build 2>&1; then
            success "Docker images built successfully"
        else
            # Fallback to docker-compose (v1)
            if docker-compose build 2>&1; then
                success "Docker images built successfully (docker-compose v1)"
            else
                error "Docker build failed"
                exit 1
            fi
        fi
    fi
else
    info "Skipping Docker build (--skip-build)"
fi

# ── Step 7: Deploy ───────────────────────────────────────────────────────────
header "Step 7: Deploying"

if $DRY_RUN; then
    info "Would run: docker compose up -d"
    echo ""
    success "Dry run complete — all validations passed"
    echo ""
    info "To deploy for real, run: ./setup.sh"
    exit 0
fi

info "Starting NOVA-7 services..."
if docker compose up -d 2>&1; then
    success "Services started with docker compose"
elif docker-compose up -d 2>&1; then
    success "Services started with docker-compose"
else
    error "Failed to start services"
    exit 1
fi

# ── Step 8: Health check ─────────────────────────────────────────────────────
header "Step 8: Health check"

APP_PORT="${APP_PORT:-8080}"
info "Waiting for NOVA-7 to become healthy on port $APP_PORT..."

MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$APP_PORT/health" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        success "NOVA-7 is healthy!"
        break
    fi
    RETRY=$((RETRY + 1))
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    warn "Health check timed out — the service may still be starting"
    info "Check logs with: docker compose logs -f nova7"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
header "Deployment Complete"

echo -e "  ${GREEN}Dashboard:${NC}      http://localhost:$APP_PORT/dashboard"
echo -e "  ${GREEN}Chaos UI:${NC}       http://localhost:$APP_PORT/chaos"
echo -e "  ${GREEN}Health:${NC}         http://localhost:$APP_PORT/health"
echo -e "  ${GREEN}API Status:${NC}     http://localhost:$APP_PORT/api/status"
echo ""
echo -e "  ${CYAN}Logs:${NC}           docker compose logs -f nova7"
echo -e "  ${CYAN}Stop:${NC}           ./teardown.sh"
echo ""
success "NOVA-7 is GO for launch!"
