---
name: "chore: Clean up dead code in archive/"
about: Good first issue — code cleanup task
labels: ["good first issue", "chore", "Ring-4"]
assignees: ''
---

## Task

Remove deprecated and dead code from the `archive/` directory that is no longer referenced by any active code.

## Context

The `archive/dead/` directory contains 3 deprecated modules (~744 lines):
- `a2a_server.py` (436 lines) — abandoned A2A protocol server
- `feishu_ws_client.py` (151 lines) — abandoned Feishu WebSocket client
- `graph_builder.py` (157 lines) — abandoned graph builder

These files are not imported anywhere in the codebase and add confusion for new contributors.

## Acceptance Criteria

1. Verify that none of the 3 files are imported by any active code:
   ```bash
   grep -r "a2a_server\|feishu_ws_client\|graph_builder" --include="*.py" . --exclude-dir=archive
   ```

2. If confirmed unused, delete the 3 files from `archive/dead/`

3. Check if `archive/dead/` has a README or index that references these files — update if so

4. Verify tests still pass after deletion:
   ```bash
   python -m pytest tests/ -x
   ```

## Skills Required

- Basic Python knowledge
- grep/find commands
- No architectural decisions needed

## Estimated Time

1-2 hours

## How to Claim

Comment `/claim` on this issue. You have 8 hours to open a WIP PR.
