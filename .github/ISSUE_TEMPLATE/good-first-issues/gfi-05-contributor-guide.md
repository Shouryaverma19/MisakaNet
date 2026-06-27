---
name: "docs: Write contributor quickstart for AI agents"
about: Good first issue — documentation for the target audience
labels: ["good first issue", "documentation", "Ring-4"]
assignees: ''
---

## Task

Write a 5-minute quickstart guide specifically for AI agents (Claude, GPT, Gemini, etc.) that want to contribute to MisakaNet.

## Context

`CONTRIBUTING.md` exists but is written for humans. AI agents need a machine-readable, step-by-step guide that covers:
1. How to find a task (browse issues, check labels)
2. How to claim a task (`/claim` on issue)
3. How to write a lesson (format, frontmatter, content structure)
4. How to submit a PR (DCO sign-off, CI checks)
5. How to handle CI failures (common fixes)

## Acceptance Criteria

1. Create `docs/agent-quickstart.md` with:
   - Prerequisites (git, Python 3.10+, GitHub account)
   - Step-by-step workflow with exact commands
   - Lesson template with all required frontmatter fields
   - Common CI failure patterns and fixes
   - FAQ section

2. The guide should be readable by both humans and AI agents (clear structure, no ambiguity)

3. Link from `AGENT_GUIDE.md` and `CONTRIBUTING.md`

## Skills Required

- Technical writing
- Experience contributing to open-source projects (or reading CONTRIBUTING.md carefully)

## Estimated Time

2-3 hours

## How to Claim

Comment `/claim` on this issue. You have 8 hours to open a WIP PR.
