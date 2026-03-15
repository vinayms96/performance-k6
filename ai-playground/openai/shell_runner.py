import subprocess
import os
import re
import time

# All shell commands run relative to this directory
SHELL_CWD = os.path.dirname(os.path.abspath(__file__))  # ai-playground/openai/

SHELL_TOOL = {
    "type": "shell",
    "environment": {"type": "local"}
}

# Framework source directories — must never be written to by the model.
# Only ../../ai-performance/ and ../../.env are writable outputs.
FRAMEWORK_READ_ONLY_DIRS = [
    os.path.normpath(os.path.join(SHELL_CWD, "..", "..", "data")),
    os.path.normpath(os.path.join(SHELL_CWD, "..", "..", "helpers")),
    os.path.normpath(os.path.join(SHELL_CWD, "..", "..", "config")),
    os.path.normpath(os.path.join(SHELL_CWD, "..", "..", "tests")),
]


def _snapshot_files(dirs: list[str]) -> dict[str, bytes]:
    """Return {filepath: content} for all files currently in the given directories."""
    files: dict[str, bytes] = {}
    for d in dirs:
        if os.path.isdir(d):
            for name in os.listdir(d):
                full = os.path.join(d, name)
                if os.path.isfile(full):
                    with open(full, "rb") as f:
                        files[full] = f.read()
    return files


def _find_ts_files(root: str) -> list[str]:
    """Recursively find all .ts files under root."""
    found = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(".ts"):
                found.append(os.path.join(dirpath, name))
    return found


# Hardcoding violation patterns applied to every generated .ts file.
# Each entry: (regex, human-readable message)
HARDCODING_VIOLATIONS = [
    (
        r'^\s*vus\s*:\s*\d+',
        "hardcoded 'vus: <number>' — import and spread the scenario object from "
        "config/scenarios.ts (e.g. { ...constantVUs }). It already reads __ENV.VUS.",
    ),
    (
        r'^\s*duration\s*:\s*[\'"]',
        "hardcoded 'duration: \"...\"' — import and spread the scenario object from "
        "config/scenarios.ts. It already reads __ENV.DURATION.",
    ),
    (
        r'^\s*iterations\s*:\s*\d+',
        "hardcoded 'iterations: <number>' — import and spread the scenario object from "
        "config/scenarios.ts. It already reads __ENV.ITERATIONS.",
    ),
    (
        r'const\s+BASE_URL\s*=',
        "hardcoded BASE_URL constant — import 'urls' from data/constants.ts and use "
        "urls.baseUrl instead.",
    ),
    (
        r'password\s*:\s*[\'"][^\'"]+[\'"]',
        "hardcoded password value — use __ENV.PASSWORD instead (or login() helper for "
        "the Notes API).",
    ),
    (
        r'email\s*:\s*[\'"][^\'"]+[\'"]',
        "hardcoded email value — use __ENV.EMAIL or import from data/users.ts instead.",
    ),
]


MAX_LOOP_ITERATIONS = 20
MAX_TEXT_REPROMPTS = 3   # re-prompts when model dumps code as text
MAX_VIOLATION_FIXES = 3  # re-prompts when hardcoding violations remain after generation


def _has_code_block(text: str) -> bool:
    """
    Returns True only if the response contains an actual multiline code block
    (triple-backtick fence with at least 3 lines of content).
    Avoids false positives on summary text that mentions 'import' or 'export'
    in plain sentences.
    """
    blocks = re.findall(r'```[\w]*\n(.*?)```', text, re.DOTALL)
    return any(block.count('\n') >= 3 for block in blocks)


def _scan_all_violations(ai_perf_root: str, shell_cwd: str) -> list[str]:
    """
    Scan every .ts file under ai_perf_root for hardcoding violations.
    Returns a list of formatted violation report strings (one per file).
    """
    reports = []
    if not os.path.isdir(ai_perf_root):
        return reports
    for ts_path in _find_ts_files(ai_perf_root):
        with open(ts_path) as f:
            lines = f.readlines()
        found = []
        for i, line in enumerate(lines, 1):
            for pattern, message in HARDCODING_VIOLATIONS:
                if re.search(pattern, line):
                    found.append(f"  Line {i}: {message}\n    → {line.rstrip()}")
        if found:
            rel_path = os.path.relpath(ts_path, shell_cwd)
            report = "\n".join(found)
            print(f"  [warn] Hardcoding violations in {rel_path}:\n{report}")
            reports.append(
                f"VIOLATION in {rel_path}:\n{report}\n\n"
                "Fix rules:\n"
                "1. NEVER hardcode vus/duration/iterations — import and spread the scenario object "
                "from config/scenarios.ts (use ../../config/ for framework API, ../config/ for custom API). "
                "The scenario object already reads all values from __ENV.\n"
                "   CORRECT: scenarios: { load: { ...constantVUs } }\n"
                "   WRONG:   vus: 5, duration: '30s'\n"
                "2. NEVER hardcode BASE_URL — import 'urls' from data/constants.ts "
                "(../../data/ for framework API, ../data/ for custom API) and use urls.baseUrl.\n"
                "3. NEVER hardcode email or password — use __ENV.PASSWORD / __ENV.EMAIL, "
                "or for the Notes API use the login() helper from helpers/setup.ts.\n"
                f"Overwrite {rel_path} using heredoc with a corrected version that fixes all violations above."
            )
    return reports


def _api_call_with_retry(client, **kwargs):
    """Call client.responses.create with exponential backoff on rate-limit and timeout errors."""
    delay = 5
    for attempt in range(5):
        try:
            return client.responses.create(**kwargs)
        except Exception as exc:
            status = getattr(exc, 'status_code', None)
            exc_type = type(exc).__name__
            is_rate_limit = status == 429 or '429' in str(exc)
            is_timeout = 'Timeout' in exc_type or 'timeout' in str(exc).lower()
            is_server_error = status is not None and status >= 500
            if is_rate_limit:
                wait = delay * (2 ** attempt)
                print(f"  [rate-limit] 429 — waiting {wait}s before retry {attempt + 1}/5...")
                time.sleep(wait)
            elif is_timeout:
                wait = delay * (2 ** attempt)
                print(f"  [timeout] request timed out — waiting {wait}s before retry {attempt + 1}/5...")
                time.sleep(wait)
            elif is_server_error:
                wait = delay * (2 ** attempt)
                print(f"  [server-error] {status} — waiting {wait}s before retry {attempt + 1}/5...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("API retry exhausted after 5 attempts")


def run_shell_loop(client, model: str, initial_response) -> str:
    """
    Agentic loop: executes shell commands the model requests, feeds results back,
    and repeats until the model returns a plain text response.

    Guard execution order:
      During generation (tool calls present):
        Guard 1 — framework source write protection   [runs every iteration]
        Guard 2 — stray files in playground dir       [runs every iteration]
        Guard 3 — hardcoding violations               [SKIPPED — model is still generating]

      After generation (no tool calls, model is done):
        Guard 3 — hardcoding violations               [runs once over ALL files]
        If violations found → re-prompt; model fixes everything in one pass
        then re-check (up to MAX_VIOLATION_FIXES rounds)

    This lets the model finish writing all files without being interrupted
    mid-generation by violation notices.
    """
    response = initial_response
    loop_count = 0
    text_reprompt_count = 0
    violation_fix_count = 0

    ai_perf_root = os.path.normpath(os.path.join(SHELL_CWD, "..", "..", "ai-performance"))

    # Snapshot framework source files before the loop so we can detect any additions.
    known_framework_files = _snapshot_files(FRAMEWORK_READ_ONLY_DIRS)

    while loop_count < MAX_LOOP_ITERATIONS:
        loop_count += 1
        tool_calls = [item for item in response.output if item.type == 'shell_call']

        # ── No tool calls: model has finished generating ────────────────────────
        if not tool_calls:
            # Guard 3: scan ALL generated files for hardcoding violations now that
            # generation is complete. Interrupt only if something is genuinely wrong.
            violations = _scan_all_violations(ai_perf_root, SHELL_CWD)
            if violations:
                if violation_fix_count >= MAX_VIOLATION_FIXES:
                    return f"(gave up after {MAX_VIOLATION_FIXES} violation-fix rounds — violations remain)"
                violation_fix_count += 1
                combined = "\n\n---\n\n".join(violations)
                print(f"  [Guard 3] Violations found — fix round {violation_fix_count}/{MAX_VIOLATION_FIXES}")
                response = _api_call_with_retry(
                    client,
                    model=model,
                    previous_response_id=response.id,
                    input=(
                        f"Generation is complete but {len(violations)} file(s) contain hardcoding violations "
                        f"that must be fixed before we can finish:\n\n{combined}\n\n"
                        "Fix ALL violations above by overwriting each file with a corrected heredoc. "
                        "Do not add new files — only fix the violations listed."
                    ),
                    tools=[SHELL_TOOL]
                )
                continue

            # No violations — check for the rare case the model dumped code as text
            # instead of writing files. Only trigger on actual multiline code blocks,
            # not on summary text that mentions keywords like 'import' in sentences.
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            text = content.text
                            if _has_code_block(text):
                                if text_reprompt_count >= MAX_TEXT_REPROMPTS:
                                    return f"(gave up after {MAX_TEXT_REPROMPTS} re-prompts — model kept returning code as text)"
                                text_reprompt_count += 1
                                print(f"  [warn] Model returned code as text — re-prompting (attempt {text_reprompt_count}/{MAX_TEXT_REPROMPTS})")
                                response = _api_call_with_retry(
                                    client,
                                    model=model,
                                    previous_response_id=response.id,
                                    input=(
                                        "You returned code as text instead of writing it to disk. "
                                        "Use shell heredoc commands to write the files now.\n\n"
                                        "CRITICAL PATH RULES:\n"
                                        "1. Every file path MUST start with ../../ai-performance/ — NEVER write to the current directory.\n"
                                        "2. For framework API: test script goes to ../../ai-performance/tests/<name>.ts\n"
                                        "3. For custom API: also create supporting files in ../../ai-performance/data/, "
                                        "../../ai-performance/helpers/, ../../ai-performance/config/ as needed.\n"
                                        "4. Always use .ts extension, NEVER .js\n"
                                        "5. Run mkdir -p on the target folder before each cat > command.\n\n"
                                        "Example:\n"
                                        "  mkdir -p ../../ai-performance/tests\n"
                                        "  cat > ../../ai-performance/tests/<name>.ts << 'ENDOFFILE'\n"
                                        "  <content>\n"
                                        "  ENDOFFILE\n\n"
                                        "Do not output any code as text — write everything to disk only."
                                    ),
                                    tools=[SHELL_TOOL]
                                )
                                break
                            else:
                                return text
                    else:
                        continue
                    break
            else:
                return "(no text output)"
            continue

        # ── Tool calls present: model is still generating ───────────────────────
        tool_results = []
        for call in tool_calls:
            action = call.action
            commands = action.commands if hasattr(action, 'commands') else [str(action)]

            outputs = []
            for command in commands:
                # Guard: reject commands that try to cd into ai-playground/openai/ (already there)
                if re.search(r'\bcd\s+ai-playground\b', command):
                    msg = (
                        "ERROR: Do not use 'cd ai-playground' — the shell already runs from ai-playground/openai/. "
                        "Use ../../ paths directly (e.g. 'cat ../../tests/e2e.ts', 'mkdir -p ../../ai-performance/tests'). "
                        "Remove the 'cd ai-playground &&' prefix and reissue the command."
                    )
                    print(f"  [shell] {command}")
                    print(f"  [blocked] {msg}")
                    outputs.append({
                        "stdout": "",
                        "stderr": msg,
                        "outcome": {"type": "exit", "exit_code": 1}
                    })
                    continue

                print(f"  [shell] {command}")
                result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=SHELL_CWD)
                print(f"  [out]   {(result.stdout or result.stderr).strip()}")
                outputs.append({
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "outcome": {"type": "exit", "exit_code": result.returncode}
                })

            result_item = {
                "type": "shell_call_output",
                "call_id": call.call_id,
                "output": outputs
            }
            if hasattr(action, 'max_output_length') and action.max_output_length is not None:
                result_item["max_output_length"] = action.max_output_length

            tool_results.append(result_item)

        # ── Guard 1: Framework source write protection ──────────────────────────
        current_framework_files = _snapshot_files(FRAMEWORK_READ_ONLY_DIRS)
        new_framework_files = set(current_framework_files) - set(known_framework_files)
        modified_framework_files = {
            path for path in current_framework_files
            if path in known_framework_files
            and current_framework_files[path] != known_framework_files[path]
        }
        if new_framework_files or modified_framework_files:
            violation_parts = []
            if new_framework_files:
                rel = [os.path.relpath(f, SHELL_CWD) for f in new_framework_files]
                print(f"  [error] Model created files in framework dirs: {rel} — deleting")
                for f in new_framework_files:
                    os.remove(f)
                violation_parts.append(f"created new files: {rel}")
            if modified_framework_files:
                rel = [os.path.relpath(f, SHELL_CWD) for f in modified_framework_files]
                print(f"  [error] Model modified framework files: {rel} — restoring originals")
                for f in modified_framework_files:
                    with open(f, "wb") as out:
                        out.write(known_framework_files[f])
                violation_parts.append(f"modified existing files: {rel}")
            known_framework_files = _snapshot_files(FRAMEWORK_READ_ONLY_DIRS)
            tool_results.append({
                "type": "message",
                "role": "user",
                "content": (
                    f"FRAMEWORK VIOLATION: You {' and '.join(violation_parts)} inside protected "
                    "framework source directories. Those changes have been reverted. "
                    "The framework source files are READ-ONLY — never create or modify anything "
                    "inside ../../data/, ../../helpers/, ../../config/, or ../../tests/.\n\n"
                    "ALL generated files MUST go inside ../../ai-performance/:\n"
                    "  - Framework API (api_type: framework): only ../../ai-performance/tests/<name>.ts\n"
                    "  - Custom API (api_type: custom): create supporting files inside "
                    "../../ai-performance/data/, ../../ai-performance/helpers/, ../../ai-performance/config/, "
                    "and the test script in ../../ai-performance/tests/<name>.ts\n\n"
                    "Re-write the files to the correct paths under ../../ai-performance/."
                )
            })

        # ── Guard 2: Stray files in ai-playground/openai/ ──────────────────────
        allowed_in_cwd = {"openai-script.py", "shell_runner.py", "requirements.txt", "PLAN.md"}
        stray_files = [
            f for f in os.listdir(SHELL_CWD)
            if os.path.isfile(os.path.join(SHELL_CWD, f))
            and f not in allowed_in_cwd
            and not f.startswith(".")
        ]
        if stray_files:
            print(f"  [warn] Stray files in ai-playground/openai/: {stray_files} — removing and re-prompting")
            for f in stray_files:
                os.remove(os.path.join(SHELL_CWD, f))
            tool_results.append({
                "type": "message",
                "role": "user",
                "content": (
                    f"ERROR: You wrote {stray_files} to the current directory (ai-playground/openai/) "
                    "instead of ../../ai-performance/. Those files have been deleted.\n"
                    "Re-write them to the correct path: ../../ai-performance/tests/<name>.ts "
                    "(or ../../ai-performance/data/, helpers/, config/ for custom API supporting files)."
                )
            })

        # Guard 3 intentionally omitted here — runs after generation is complete.

        # Feed results back to the model
        response = _api_call_with_retry(
            client,
            model=model,
            previous_response_id=response.id,
            input=tool_results,
            tools=[SHELL_TOOL]
        )

    return f"(loop limit of {MAX_LOOP_ITERATIONS} iterations reached — agent did not finish)"
