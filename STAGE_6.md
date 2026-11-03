# CoachBot AI — Stage 6

Implemented the evaluation harness, synthetic edge-case fixtures, a blank student
quality rubric and a short exploration notebook. English remains the default.
The original one worked prompt is unchanged; the other nine remain yours to author.
The current provider is Groq, using strict JSON Schema with `openai/gpt-oss-20b`.

## Start with a zero-call plan

Run commands from the project root, using the environment set up in Stage 1:

```powershell
.\.venv\Scripts\python.exe -m eval.eval_runner
.\.venv\Scripts\python.exe -m eval.eval_runner --subset 3
```

No key or model is needed for planning. Without `--execute`, no provider is opened
and no evaluation result files are written. `--subset N` selects the first N
**jobs**, not cases. Order is prompt, case, temperature, top_p, then max_tokens.
Use a smaller cases file to target a particular edge case. Latest registry
versions run by default; `--all-versions` includes historical versions.

### Call count before running

The full grid is 3 temperatures (0.2, 0.5, 0.9), 2 top_p values (0.8, 0.95) and
3 max_tokens limits (256, 512, 1024): **18 configurations per case**. The current
default model is `openai/gpt-oss-20b`; Groq documents strict JSON Schema support
and sampling parameters for it. Confirm that the model appears for your Groq key
before any live call.

The eight synthetic cases and one registered prompt produce **144 jobs**:
**90 local checks use zero calls** and **54 are model-eligible**. On a fresh cache,
expect about **54 calls** if each eligible request succeeds first time. Schema
repairs without transport retries can raise that to 108; the configured worst-case
ceiling is **324 attempted calls** (six per eligible job). These are planning bounds,
not observed provider usage. Quota availability and model behavior vary. The default
shared budget caps each invocation at **12 attempted calls**, including
repairs and retries. A completed identical rerun uses **zero calls**.

For `--subset 3`, the exact estimate depends on whether the selected jobs pass local
checks. The planner prints eligible calls and their retry ceiling before execution.
Model, inputs, code, prompt version or parameter changes invalidate checkpoint
identity. Planning reads checkpoints, not the private client response cache, so
its call estimate is conservative if a response cache exists without a checkpoint.

## Execute deliberately after private setup

Verify the default `openai/gpt-oss-20b` appears for your Groq key with
`check_models.py` and configure the key privately as described in Stage 1. If you
select a different model, update `MODEL_NAME` in `config.py`. No API key is included
in this project.

```powershell
.\.venv\Scripts\python.exe -m eval.eval_runner --subset 3 --max-calls 3 --sleep 2 --execute
```

The call cap can stop before all three jobs finish if retries or repairs are used.
Run the same command again to continue pending jobs. Saved transient failures are
not retried automatically. After resolving the quota/access/network issue:

```powershell
.\.venv\Scripts\python.exe -m eval.eval_runner --subset 3 --max-calls 3 --sleep 5 --retry-failed --execute
```

`--sleep` delays every actual Groq HTTP attempt, including repair/retry attempts; the
client also uses its existing bounded exponential backoff. A rate-limit failure
stops the sweep after the wrapper's bounded retries. Completed results remain.
Repeated complete runs do not construct a client or need credentials. No fresh
sampling flag is supplied: use a separate output directory for a deliberate new
experiment and account for new calls. Run only one evaluator per output directory
at a time. Do not share output/cache directories between users.

Optional grid overrides:

```powershell
.\.venv\Scripts\python.exe -m eval.eval_runner --temperatures 0.2 0.5 0.9 --top-p 0.8 0.95 --max-tokens 256 512 1024
```

## Your own cases

Copy `eval/cases.student.template.json`, replace every placeholder, and pass
`--cases eval/my_cases.json`. Provide actual booleans for health flags, one of
`none`, `reported`, `unknown` for injury_status, and an array of injury-region
labels (see `core/safety.py`). Supply exact registered input fields as strings.
The file must be a JSON array with unique case IDs. Keep private cases under
`data/` and pass that path if they contain personal information. Prefer fictional
or anonymized examples. The template deliberately refuses to execute unchanged.

See [edge-case checklist and unscored rubric](docs/EVAL_CASE_CHECKLIST.md).
Your research, case selection rationale, scores, observations and conclusions
remain **[MY INPUT NEEDED]**. Synthetic engineering fixtures are not student findings.

## Outputs and interpretation

All generated outputs are private/ignored under `eval/results/`:

- `checkpoints/<job-id>.json`: atomic latest record, authoritative for resume.
- `receipts/*.json`: historical result records, including retried failures.
- `runs.jsonl`: rebuilt log of the selected jobs, including every attempt's raw
  output, status, finish reason, latency, token counts and schema-valid flag.
- `summary.csv`: one row per recorded job; no raw text.
- `tuning.csv`: grouped prompt/version/language/temperature/top_p/max_tokens table
  showing output length, token-limit rate and structural completeness.

CSV files are rebuilt views, not the resume source. A damaged CSV/JSONL is rebuilt
from checkpoints. Corrupt checkpoints stop the runner for inspection rather than
silently making another paid request. A process killed between receiving a
provider response and saving its cache/checkpoint can require another call;
exactly-once billing cannot be guaranteed across that interruption window.

`initial_output_chars` and `final_output_chars` distinguish the first response
from its repair. Initial/final output-token counts measure each corresponding
attempt; `output_tokens`, `input_tokens` and `thinking_tokens` sum all attempts
when all counts are known (otherwise blank). `final_whitespace_words` is only a
rough text-length measure and is not comparable across every language. Stored
`calls_made` and latencies describe the recorded job; the console reports calls
in the current invocation. Client-cache hits preserve historical attempt metrics.

`complete_structured_response` means the core client accepted a complete schema,
matching language label and normal STOP finish. It does **not** mean the content
fully answers the question, is correct, or is safe. The schema-valid flag follows
that same client validation convention, not JSON syntax alone. Safety screening
is reported separately in `display_state`. Local notices are excluded from model
quality rates and have blank schema-valid metrics. Token-limit flags survive a
successful repair, so the CSV does not hide initial truncation. Inspect initial
and final columns together when comparing max_tokens values. Each configuration
has only one cached sample per case; this is not a statistical significance test.

Raw output can contain unsafe text or personal context. Never render it as advice
or publish raw logs. Manually review/anonymize any table before pasting it into the
Stage 7 README. No tuning conclusions have been written for you.

## Notebook companion

Open `notebooks/exploration.ipynb` in a notebook editor using the project's Python
environment. It imports `core/` and the runner; it does not duplicate client,
prompt or validation logic. It contains an opt-in one-attempt connectivity check,
a three-job sweep demonstration and an offline missing-rationale validation test.
Live cells are disabled by default. Notebook execution support belongs to your
editor; no Jupyter server dependency is needed by the deployed app.

## Verification

The 98 offline-test count and notebook execution notes below the original Stage 6
implementation describe the earlier Gemini client. They do not verify the current
Groq migration. This update has not run the test suite or notebook cells, and no
live Groq requests, quota measurements, model-quality conclusions or cloud
deployment are claimed. The notebook remains configured with live calls disabled.
