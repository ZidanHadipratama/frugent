#!/usr/bin/env python3
"""Frugent — frugal + agent. Update utility."""

import os
import subprocess
import sys
from pathlib import Path

FRUGENT_DIR = Path.home() / ".frugent"

# Colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
DIM = "\033[2m"
NC = "\033[0m"


def update():
    """Pull latest changes from repo and re-run setup."""
    repo_path_file = FRUGENT_DIR / ".repo_path"

    if not repo_path_file.exists():
        print(f"  {RED}Cannot update — repo path not found.{NC}")
        print(f"  Re-install with: cd /path/to/frugent && bash setup.sh")
        sys.exit(1)

    repo_path = repo_path_file.read_text().strip()
    if not Path(repo_path).is_dir():
        print(f"  {RED}Repo not found at {repo_path}{NC}")
        print(f"  Re-install with: cd /path/to/frugent && bash setup.sh")
        sys.exit(1)

    print(f"  {BOLD}Updating Frugent...{NC}")
    print(f"  {DIM}Repo: {repo_path}{NC}")
    print()

    # Git pull
    result = subprocess.run(
        ["git", "pull"], cwd=repo_path, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  {RED}git pull failed:{NC}")
        print(f"  {result.stderr.strip()}")
        sys.exit(1)

    pull_output = result.stdout.strip()
    if "Already up to date" in pull_output:
        print(f"  {GREEN}Already up to date.{NC}")
        return

    print(f"  {GREEN}Pulled latest changes:{NC}")
    print(f"  {DIM}{pull_output}{NC}")
    print()

    # Re-run setup.sh
    setup_script = Path(repo_path) / "setup.sh"
    if not setup_script.exists():
        print(f"  {RED}setup.sh not found in repo{NC}")
        sys.exit(1)

    print(f"  Running setup.sh...")
    print()
    os.execvp("bash", ["bash", str(setup_script)])


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("update", "--update"):
        update()
    elif args[0] in ("help", "--help", "-h"):
        print()
        print(f"  {BOLD}Frugent{NC} — frugal + agent")
        print()
        print(f"  {BOLD}Usage:{NC}")
        print(f"    frugent update     Pull latest version and re-install")
        print(f"    frugent help       Show this help")
        print()
        print(f"  {BOLD}Slash commands (run inside claude/gemini/codex):{NC}")
        print(f"    /frugent-init      Initialize project")
        print(f"    /frugent-plan      Create execution plan")
        print(f"    /frugent-execute   Execute tasks")
        print(f"    /frugent-handoff   Write handoff document")
        print(f"    /frugent-status    Check quota and progress")
        print()
    else:
        print(f"Unknown command: {args[0]}")
        print("Run 'frugent help' for usage")
        sys.exit(1)


if __name__ == "__main__":
    main()
