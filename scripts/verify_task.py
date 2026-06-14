#!/usr/bin/env python3
"""Verify a task by checking its source file and test command.
Usage: python3 scripts/verify_task.py <task_id>
"""
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def main():
    task_id = sys.argv[1] if len(sys.argv) > 1 else ""
    if not task_id:
        print("Usage: python3 scripts/verify_task.py <task_id>")
        sys.exit(1)

    task_file = REPO / "tasks" / f"{task_id}.json"
    if not task_file.exists():
        print(f"Task not found: {task_id}")
        sys.exit(1)

    task = json.loads(task_file.read_text())
    source = task.get("source", "")
    source_path = REPO / source

    checks = 0
    passed = 0

    # Check 1: source file exists
    checks += 1
    if source_path.exists():
        passed += 1
    else:
        print(f"  FAIL: source {source} not found")

    # Check 2: has problem
    checks += 1
    if task.get("problem"):
        passed += 1
    else:
        print(f"  FAIL: no problem field")

    # Check 3: has solution
    checks += 1
    if task.get("solution"):
        passed += 1
    else:
        print(f"  FAIL: no solution field")

    print(f"  {task['title'][:50]}")
    print(f"  source: {source} ({source_path.stat().st_size if source_path.exists() else 0} bytes)")
    print(f"  {passed}/{checks} checks passed")

    if passed == checks:
        print("  OK: task valid")
        sys.exit(0)
    else:
        print(f"  FAIL: {checks - passed} checks failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
