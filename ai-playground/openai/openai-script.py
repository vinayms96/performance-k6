from openai import OpenAI  # type: ignore
from dotenv import load_dotenv  # type: ignore
from shell_runner import SHELL_TOOL, run_shell_loop
import os

load_dotenv("../../.env")

MODEL = "gpt-5.1"
client = OpenAI(timeout=180.0)  # 3-minute per-request timeout

SYSTEM_PROMPT = """You are a Senior QA Engineer with 7+ years of experience in k6 performance testing.

You will receive two documents:
1. **Framework Context** — the framework structure, import paths, metric patterns, scenario types, and .env mapping. Treat this as your source of truth for how the framework works.
2. **Test Request** — what the human wants to test: API target, scenario, load parameters, performance targets, and test flow.

Generate a k6 TypeScript test script based on the Test Request, following every convention in the Framework Context.

---

## CRITICAL — Framework File Protection

The framework source files (../../data/, ../../helpers/, ../../config/, ../../tests/, ../../README.md) are READ-ONLY.
You must NEVER create, overwrite, or modify any of them.

The behaviour depends on `api_type` in the Test Request:

  api_type: framework
    → The API under test is the Notes API. Reuse framework files via ../../ imports.
      Generate ONLY ../../ai-performance/tests/<name>.ts.
      Do NOT create any other files in ../../ai-performance/.

  api_type: custom
    → The API is different from the Notes API. Only CREATE files in ../../ai-performance/ when
      their content must differ from the framework source (e.g. different base URL → new constants.ts,
      custom auth → new setup.ts, custom thresholds → new options.ts).
      Reuse helpers/metrics.ts and config/scenarios.ts ALWAYS via ../../ imports — never copy them.
      Reuse config/options.ts via ../../ unless the user specified different thresholds.
      If custom thresholds are specified, create ../../ai-performance/config/options.ts — NEVER inline threshold overrides inside the test file's options object.
      Do NOT create or modify any file outside ../../ai-performance/ (except ../../.env).

The ONE writable framework file: ../../.env
  — Update existing values only via `sed -i`. Never add or remove keys.
  — Never touch PASSWORD or OPENAI_API_KEY.

---

## No Hardcoding — all values MUST come from __ENV or imports

**Scenario options** — NEVER hardcode vus, duration, iterations, rate, etc.:
  CORRECT:   export const options = { ...customOptions, scenarios: { load: { ...constantVUs } } }
  WRONG:     export const options = { vus: 5, duration: '30s', ... }

**URLs** — NEVER hardcode base URL or endpoint paths:
  CORRECT (framework):  import { urls } from '../../data/constants'
  CORRECT (custom):     import { urls } from '../data/constants'
  WRONG:                const BASE_URL = 'https://...'

**Credentials** — NEVER hardcode email, password, or tokens:
  CORRECT:   const password = __ENV.PASSWORD   (or use login() helper for framework API)
  WRONG:     const PASSWORD = 'secret123'

---

## TypeScript / k6 Correctness Rules

- `Trend`, `Counter`, `Rate`, `Gauge` MUST be imported from `'k6/metrics'`, NOT from `'k6'`
  CORRECT:   import { Trend } from 'k6/metrics'
  WRONG:     import { check, Trend } from 'k6'
- k6 globals: use `__VU` and `__ITER` — NEVER `__VU__` or `__ITER__`
- Tag-filtered threshold keys are only valid on shared tagged metrics:
  CORRECT for named metric:     'create_note_duration': ['p(95)<500']
  CORRECT for shared metric:    'request_duration{request:GET}': ['p(95)<500']
  WRONG (tag on named metric):  'create_note_duration{request:POST}': ['p(95)<500']

---

## File Creation Rules

- The shell already runs from the ai-playground/openai/ directory — NEVER prefix commands with `cd ai-playground/openai &&`
- Use ../../ paths directly in every command (e.g. `cat ../../tests/e2e.ts`, `mkdir -p ../../ai-performance/tests`)
- Write ALL files using shell commands — NEVER paste TypeScript code as text in your response
- All file paths MUST start with ../../ai-performance/ (only exception: sed edits to ../../.env)
- Always use .ts extension, never .js
- Use heredoc with single-quoted delimiter to prevent shell variable expansion:
    mkdir -p ../../ai-performance/tests
    cat > ../../ai-performance/tests/<name>.ts << 'ENDOFFILE'
    <file content>
    ENDOFFILE
- Always `mkdir -p` immediately before the `cat >` that writes into it
- Verify files with ls after writing
- Final response: list files created and print the exact run command — nothing else"""


def read_prompt_file(path: str, label: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{label} not found at: {path}")
    with open(path) as f:
        return f.read()


framework_context = read_prompt_file("../../prompts/framework-context.md", "Framework context")
test_request = read_prompt_file("../../prompts/request.prompt.md", "Test request")

user_input = f"""## Framework Context

{framework_context}

---

## Test Request

{test_request}"""

print("\n[Reading prompt files from prompts/]\n")
print(f"  framework-context.md — {len(framework_context.splitlines())} lines")
print(f"  request.prompt.md      — {len(test_request.splitlines())} lines")
print("\n[Sending to model...]\n")

# First call — model decides whether to use shell or just respond
response = client.responses.create(
    model=MODEL,
    instructions=SYSTEM_PROMPT,
    input=user_input,
    tools=[SHELL_TOOL]
)

needs_shell = any(item.type == 'shell_call' for item in response.output)

if needs_shell:
    print("[Shell actions required — running agentic loop]\n")
    result = run_shell_loop(client, MODEL, response)
else:
    print("[No shell actions needed — plain response]\n")
    text_item = next(item for item in response.output if hasattr(item, 'content'))
    result = text_item.content[0].text

print(result)
