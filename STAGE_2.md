# CoachBot AI — Stage 2

The original Gemini client described in this stage has been replaced by
`core/groq_client.py`. The response contract in `core/schemas.py` remains active.
The setup screen remains a setup screen. Prompt registry, content safety checks,
recommendation rendering and the evaluation runner arrive in later stages.

## What the schemas enforce

Each recommendation contains `title`, `action` and a mandatory, nonblank
`rationale` of at most 600 characters. The rationale is a short explanation for
the user, not a request for private model reasoning. The response contains:

```text
status: suggestions | needs_clarification | professional_referral
language: exact selected language label
recommendations: 1–12 objects, each with title, action, rationale
follow_up_questions: 0–3 questions
```

Unexpected fields, empty required text and invalid parameter ranges are rejected.
The same contract supports different coaching features without allowing a second
recommendation format that omits rationales. Questions are for clarification only.

English is the default, even if the input is written in another language. An
explicit language selection changes human-readable values; keys and status enums
stay English. The client validates the language label. This does not automatically
prove that every sentence is written fluently in that language.

## Request and response flow

1. The future registry supplies a `GenerationRequest` with prompt ID, version,
   rendered prompt, constraints, language and generation parameters.
2. `GroqClient.from_streamlit()` reads `[groq].api_key` through `st.secrets`.
   Missing secrets and an unset model raise a friendly `SetupError` for the UI.
3. The client looks for a matching response in the private on-disk cache.
4. A cache miss calls the Groq Chat Completions API with a strict JSON Schema.
5. The output must finish normally, parse as JSON and pass the Pydantic schema.
   Invalid or truncated output gets one fresh schema-repair attempt at the same
   parameters. Original and repaired outputs remain separate diagnostic records.
6. A second invalid result returns `validation_error` with `data=None`. Blocked
   results are not repaired. No raw or partial response should appear in the UI.
7. Stage 4 must check content safety before Stage 5 renders `result.data`.

The current HTTP request includes:

```python
{
    "model": config.MODEL_NAME,
    "temperature": request.parameters.temperature,
    "top_p": request.parameters.top_p,
    "max_completion_tokens": request.parameters.max_tokens,
    "response_format": {"type": "json_schema", "json_schema": {"strict": True, "schema": ...}},
}
```

## Retry and quota behavior

- Each HTTP attempt has a 30-second request timeout. This is not a total-operation
  deadline: retries, repair and pauses can make a request take longer.
- HTTP 429, temporary service failures and connection/time-out failures can retry,
  up to three attempts per phase. Backoff doubles with a small random jitter.
- Authentication, unavailable models and other invalid requests do not retry.
  Recognized invalid-key errors returned as HTTP 400 are treated as authentication
  failures. Provider exception text is never exposed.
- The HTTP client has no hidden retry policy, so every attempt is counted.
- A normal valid response needs **one** generation attempt; one repair needs
  **two** without transport failures. The default worst case is **six** attempts.
- `CallBudget(limit=...)` can be shared across sequential requests. It counts
  failed attempts and repairs. Reaching the limit prevents the next API call.
- `sleep_seconds` pauses before each network attempt; cache reads do not sleep.
- The later evaluation harness will add `--subset`, resumable job scheduling,
  a pre-run count and the CSV grid. Those are not implemented in Stage 2.

## Caching and logging

The cache key includes model, full request, prompt version, parameters, language,
constraints, schema and client-policy version. UI sessions use separate random
namespaces. Offline evaluation must use the same private namespace on reruns.

Completed valid, blocked and validation-failure results are cached. Exact repeats
with intact cache files use zero generation calls. Cached failure results remain
failures. `use_cache=False` requests a fresh sample without replacing the existing
cache. Errors such as a rate limit are not cached permanently.

Raw responses exist only in returned diagnostics and the ignored local cache;
they may contain personal information. Cache namespaces prevent accidental
cross-session reuse but are not encryption or a replacement for access controls.
Do not commit or share cache files. The metadata JSONL log omits input text,
responses, credentials and provider error messages. Each completed attempt is
appended immediately; the full resumable evaluation log comes in Stage 6.

Cache writes use a temporary file and atomic replacement. A write failure keeps
the response available but adds a warning. Missing, corrupt, cleared or unwritable
caches can cause repeat calls. A crash after the provider processed a request but
before the result was saved can also require a repeat; exactly-once billing cannot
be guaranteed. Local Streamlit Cloud storage is not durable across redeployments.

## Run the offline checks

From the project folder after installing requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests use fake responses and credentials; no API key or network call is
needed. They cover schemas, English defaults, a Tamil fixture, one repair,
truncation, blocked output, retries, budgets, cache replay/isolation, write failures,
safe logging and client cleanup. These engineering fixtures are not your graded
evaluation cases, findings or quality scores.

## Current limits and next stage

The 26-test count and SDK checks recorded above applied to the original Gemini
client. They do not verify the current Groq migration. The Groq implementation
has not been live-tested; the model default is `openai/gpt-oss-20b` and account
access must be checked with `check_models.py`.

`MODEL_NAME` remains unset until you verify a model with your key. The installed
SDK accepts the configuration locally; live model capabilities, quotas and actual
output quality are unverified. Schema validation is not a medical-safety check.
Injury-aware constraints and content screening still belong to Stage 4.

The wrapper is for sequential use. Create a separate client per UI session or
evaluation process; the mutable budget and log are not a concurrency coordinator.

Stage 3 will provide the versioned registry and one worked prompt. The remaining
nine prompts, research, feedback scores and validation conclusions remain yours.

Technical references: [Groq Chat Completions API](https://console.groq.com/docs/api-reference)
and [Structured Outputs](https://console.groq.com/docs/structured-outputs).
