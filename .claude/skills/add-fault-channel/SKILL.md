---
name: add-fault-channel
description: Replace one fault channel in an existing scenario. Use when the user wants to add, swap, or improve a fault in scenarios/<id>/scenario.py. Makes four coordinated edits: channel_registry, get_fault_params, get_rca_clues, and agent_config.system_prompt. Never touches any file outside scenarios/<id>/scenario.py.
---

# Replace a fault channel

This skill replaces one existing fault channel in a scenario with a new or improved one. It makes four coordinated edits in `scenarios/<id>/scenario.py` and validates consistency.

Read [GUARDRAILS.md](GUARDRAILS.md) now and hold every rule in it for the duration of this session.

---

## Phase 1: Gather the brief

Parse any context the user already provided. Then read [BRIEF.md](BRIEF.md) and ask — via `AskUserQuestion` — only about signals that are missing. Ask at most 3 questions per call.

Required before Phase 2:
- **Scenario** — which scenario_id to modify
- **Channel number** — which channel (1–20) to replace
- **Fault description** — what the new channel should represent

---

## Phase 2: Read current state

Read `scenarios/<id>/scenario.py` in full. Extract:

1. The **current channel** at the target number (all fields)
2. The **services dict** — to know valid service keys and subsystems
3. The **agent_config.system_prompt** — to locate the error_type list that needs updating
4. The **get_fault_params** entry for this channel number
5. The **get_rca_clues** entry for this channel number

Also read [CONTRACT.md](CONTRACT.md) now as a generation checklist.

---

## Phase 3: Design — propose then confirm

Present the proposed new channel via `AskUserQuestion` (single question, long description field) and ask the user to confirm, adjust, or replace before writing any code.

The proposal must cover:

- **Channel number** being replaced, and current channel name being replaced
- **New channel name, subsystem, vehicle_section, error_type**
- **error_message** template (showing all `{placeholder}` names)
- **affected_services** and **cascade_services** (service keys, not display names)
- **remediation_action** and whether it's HITL (1–15) or auto-remediable (16–20)
- **investigation_notes** summary (key steps; full 5–6 lines in Phase 4)
- **agent_config.system_prompt** change — old error_type → new error_type

If the channel number is 16–20, confirm the `remediation_action` passes the auto-remediate test from GUARDRAILS.md §3.

---

## Phase 4: Make the four coordinated edits

After the user confirms, make all four edits using the `Edit` tool. Do not ask permission for each — make them all.

### Edit 1 — `channel_registry[N]`

Replace the entire channel dict at key `N`. Keep the key number the same.

Follow the field order in CONTRACT.md: `name`, `subsystem`, `vehicle_section`, `error_type`, `sensor_type`, `affected_services`, `cascade_services`, `description`, `investigation_notes`, `remediation_action`, `error_message`, `stack_trace`.

`investigation_notes`: 5–6 numbered steps. Reference specific log field names, metric names, and `{placeholder}` values. Tell the agent exactly what to search for and how to confirm the fix.

### Edit 2 — `get_fault_params(N)` entry

Replace the `N:` dict inside `get_fault_params`. Every `{placeholder}` in `error_message` and `stack_trace` must be a key. Use `rng` (already initialized as `random.Random(channel + int(time.time()) // 10)` at the top of the method) — do not re-initialize it.

### Edit 3 — `get_rca_clues(N, ...)` entry

Replace the `N:` dict inside `get_rca_clues`. Keys are service names from `affected_services` + `cascade_services`. Each service gets 2–3 domain-appropriate numeric or boolean attributes that suggest the root cause without naming it directly.

### Edit 4 — `agent_config` system_prompt

Find the subsystem grouping that contained the old `error_type` and remove it. Add the new `error_type` to the appropriate subsystem grouping (or create a new grouping if the subsystem is new).

Pattern used in existing scenarios:
```
"<Subsystem> faults (TYPE-A, TYPE-B, TYPE-C), "
```

---

## Phase 5: Validate

Run the CONTRACT.md checklist inline (no external script needed — inspect the edited content):

1. **Placeholder parity** — collect every `\{(\w+)\}` from the new `error_message` and `stack_trace`; confirm each is a key in `get_fault_params(N)`.
2. **Service validity** — every value in `affected_services` and `cascade_services` is a key in `services`.
3. **Channel count** — `len(channel_registry) == 20`.
4. **HITL/auto-remediate** — channel ≤ 15: HITL action; channel 16–20: plausible auto-runbook action.
5. **system_prompt sync** — new `error_type` appears in the prompt; old `error_type` (if changed) does not.

**Scope check:**
```bash
git diff --name-only
```
Output must show only `scenarios/<id>/scenario.py`. If any other file appears, stop and alert the user.

**Report:** Summarize what changed (old channel → new channel), which four locations were edited, and any validation warnings. Include the channel number and error_type for easy cross-reference.
