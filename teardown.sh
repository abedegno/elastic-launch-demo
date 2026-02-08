#!/usr/bin/env bash
# ============================================================================
# NOVA-7 Teardown Script
# ============================================================================
# Stops all containers, removes volumes, and cleans up.
# Usage:
#   ./teardown.sh              # Stop containers and remove volumes
#   ./teardown.sh --keep-data  # Stop containers but preserve volumes
#   ./teardown.sh --full       # Remove everything including images
# ============================================================================

set -euo pipefail

# ── Color helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
header()  { echo -e "\n${CYAN}══════════════════════════════════════════════════════════${NC}"; echo -e "${CYAN}  $*${NC}"; echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}\n"; }

# ── Parse arguments ──────────────────────────────────────────────────────────
KEEP_DATA=false
FULL_CLEAN=false

for arg in "$@"; do
    case "$arg" in
        --keep-data)  KEEP_DATA=true ;;
        --full)       FULL_CLEAN=true ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --keep-data   Stop containers but preserve Docker volumes"
            echo "  --full        Remove everything: containers, volumes, and images"
            echo "  -h, --help    Show this help message"
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

header "NOVA-7 Launch Demo — Teardown"

# ── Determine docker compose command ─────────────────────────────────────────
COMPOSE_CMD=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    error "Neither 'docker compose' nor 'docker-compose' found"
    exit 1
fi

info "Using: $COMPOSE_CMD"

# ── Step 1: Stop containers ─────────────────────────────────────────────────
header "Step 1: Stopping containers"

if $KEEP_DATA; then
    info "Stopping containers (preserving volumes)..."
    $COMPOSE_CMD down 2>&1 || true
    success "Containers stopped (volumes preserved)"
else
    info "Stopping containers and removing volumes..."
    $COMPOSE_CMD down -v 2>&1 || true
    success "Containers stopped and volumes removed"
fi

# ── Step 2: Remove orphan containers ────────────────────────────────────────
header "Step 2: Cleaning up orphan containers"

ORPHANS=$($COMPOSE_CMD ps -a -q 2>/dev/null || true)
if [ -n "$ORPHANS" ]; then
    info "Removing orphan containers..."
    $COMPOSE_CMD down --remove-orphans 2>&1 || true
    success "Orphan containers removed"
else
    success "No orphan containers found"
fi

# ── Step 3: Remove images (only with --full) ────────────────────────────────
if $FULL_CLEAN; then
    header "Step 3: Removing Docker images"

    info "Removing project images..."
    $COMPOSE_CMD down --rmi local 2>&1 || true
    success "Project images removed"

    # Also prune any dangling images from failed builds
    info "Pruning dangling images..."
    docker image prune -f 2>&1 || true
    success "Dangling images pruned"
else
    info "Skipping image removal (use --full to remove images)"
fi

# ── Step 4: Remove Docker networks ──────────────────────────────────────────
header "Step 4: Cleaning up networks"

PROJECT_NAME=$(basename "$SCRIPT_DIR" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
NETWORKS=$(docker network ls --filter "name=${PROJECT_NAME}" -q 2>/dev/null || true)
if [ -n "$NETWORKS" ]; then
    info "Removing project networks..."
    docker network rm $NETWORKS 2>/dev/null || true
    success "Project networks removed"
else
    success "No project networks to clean up"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
header "Teardown Complete"

if $KEEP_DATA; then
    info "Volumes were preserved. Use --full next time to remove everything."
fi

echo ""
success "NOVA-7 environment has been cleaned up"
echo ""
info "To redeploy, run: ./setup.sh"
