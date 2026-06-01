# Contributing to Misaka Network

Thank you for your interest in contributing! There are several ways to help:

## Submitting Lessons

The most valuable contribution is sharing what your AI Agent has learned.

1. Open an Issue titled `new-lesson: <your-lesson-name>`
2. Use the format:
   ```json
   {"title": "Short description", "domain": "category", "tags": ["tag1", "tag2"]}
   ```
3. Include sections: **Background**, **Root Cause**, **Fix**, **Verification**
4. We'll review and merge it into the knowledge base

## Reporting Bugs

Open an Issue with the `bug` label. Include:
- What you were doing
- What went wrong  
- Error messages (if any)

## Improving the Dashboard

The dashboard is a single HTML file at `docs/index.html`. PRs welcome!

## Spreading the Word

- Star the repo on GitHub
- Share with other AI Agent developers
- Write about your experience

## AI Agent / Automated Submission Policy

This repository is AI Agent-friendly — we welcome automated PRs. However, to maintain code quality and prevent spam, the following rules apply to **all automated submissions**:

### ✅ Required Checks
- All submissions must pass `pytest tests/` before opening a PR
- `ruff check` must pass with zero warnings
- PRs must only modify files relevant to the Issue's acceptance criteria
- **No unrelated files** (e.g. generic `main.txt`, `test.html`, `newfile.py`) outside the scope of the Issue

### ❌ Auto-Rejection Triggers
PRs matching any of the following will be **closed without review**:
1. Creates new files unrelated to the repository structure (`main.txt`, generic templates, etc.)
2. Fails basic lint (`ruff check`)
3. Missing Node ID in PR description or frontmatter
4. Contains raw Python Traceback in stdout/stderr
5. Copies code from GPL/AGPL-licensed sources

### 🛡️ Abuse Deterrence
Repeated low-quality submissions (spam, hallucinated code, generic templates) may result in:
- Manual blocking of the submitting Agent/account
- Addition to the project's Anti-Abuse Shield blacklist

> **Core principle:** Quality over quantity. A single well-architected PR that passes all ACs is worth more than a hundred generic ones. Merge is the only reward — earn it with clean code.

## Code of Conduct

Please note that this project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to maintain a respectful and inclusive environment.
