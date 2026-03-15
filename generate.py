"""
Unified k6 script generator — delegates to the correct AI playground.

Usage (from performance-k6/ root):
  python3 generate.py             # defaults to --ai claude
  python3 generate.py --ai claude
  python3 generate.py --ai openai

Structure:
  ai-playground/
  ├── .venv/           shared venv (anthropic + openai + python-dotenv)
  ├── requirements.txt
  ├── openai/          openai-script.py + shell_runner.py
  └── claude/          claude-script.py + tool_runner.py

To set up from scratch:
  python -m venv ai-playground/.venv
  ai-playground/.venv/bin/pip install -r ai-playground/requirements.txt
"""

import argparse
import subprocess
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

PLAYGROUND_MAP = {
    "claude": ("ai-playground/claude", "claude-script.py"),
    "openai": ("ai-playground/openai", "openai-script.py"),
}

VENV_PYTHON = os.path.join(ROOT, "ai-playground", ".venv", "bin", "python3")


def _resolve_python() -> str:
    """Return the shared venv python if it exists, otherwise the system interpreter."""
    if os.path.exists(VENV_PYTHON):
        return VENV_PYTHON
    print(
        "[warn] ai-playground/.venv not found — using system python.\n"
        "       To create it: python -m venv ai-playground/.venv\n"
        "                     ai-playground/.venv/bin/pip install -r ai-playground/requirements.txt\n"
    )
    return sys.executable


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a k6 TypeScript performance test using AI."
    )
    parser.add_argument(
        "--ai",
        choices=list(PLAYGROUND_MAP.keys()),
        default="claude",
        help="AI backend to use (default: claude)",
    )
    args = parser.parse_args()

    playground_subdir, script_name = PLAYGROUND_MAP[args.ai]
    playground_path = os.path.join(ROOT, playground_subdir)
    script_path = os.path.join(playground_path, script_name)

    if not os.path.exists(script_path):
        print(f"[error] Script not found: {os.path.relpath(script_path, ROOT)}")
        sys.exit(1)

    python = _resolve_python()

    print(f"\n[generate.py] AI={args.ai.upper()}  script={playground_subdir}/{script_name}\n")

    result = subprocess.run([python, script_name], cwd=playground_path)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
