# CoachBot AI — Stage 1

Stage 1 provides setup files, not a working coaching assistant. English is the
default for the interface and responses. A later explicit language selection
will change response values only; JSON schema keys remain English.

## Start on Windows

Open a terminal in this folder. Use Python 3.11 or newer (3.13 is installed on
this computer). These commands do not require changing PowerShell policy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Only copy the template if you do not already have a secrets.toml. Edit the private
file and replace YOUR_API_KEY_HERE. Do not paste the key into chat, source code,
screenshots or .env.example. The nested [groq] table is read using st.secrets.

Verify available models in the [Groq Console](https://console.groq.com/).
Run the included model check:

```powershell
.\.venv\Scripts\python.exe -m streamlit run check_models.py
```

Click List available models. The current default is `openai/gpt-oss-20b`. Verify
it is listed for your key; if it is not, replace `MODEL_NAME` in config.py with an available text
model. That is the only model-name setting. A model listing does not prove
generation quota or response quality, so submit a sample only after setup.

Stop the check with Ctrl+C, then run the setup screen:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

No generation calls occur in Stage 1. The list endpoint can make multiple paged
requests and retries. It uses a 30-second per-request timeout and at most three
attempts per request, with exponential backoff for transient failures.

## File tree and delivery boundaries

```text
coachbot-ai/
  app.py                       Stage 1 setup screen; full UI in Stage 5
  check_models.py               Runnable model-availability check
  config.py                    One model setting, English default, future defaults
  requirements.txt             Pinned direct dependencies
  .gitignore
  .env.example                 Documentation only; no dotenv loading
  .streamlit/
    config.toml
    secrets.toml.example       Safe template; real secrets.toml is ignored
  core/
    __init__.py
    groq_client.py              Current Groq request boundary
    schemas.py                  PLANNED Stage 2
    prompts.py                  PLANNED Stage 3: one example only
    safety.py                   PLANNED Stage 4
    formatter.py                PLANNED Stage 4
  ui/
    __init__.py
    components.py               PLANNED Stage 5
  eval/
    __init__.py
    eval_runner.py              PLANNED Stage 6
    results/.gitkeep
  notebooks/
    .gitkeep
    exploration.ipynb           PLANNED Stage 6; imports core/
  docs/evidence/.gitkeep
  STAGE_1.md
  README.md                     PLANNED Stage 7
```

The temporary folder name is not your final GitHub repository name.

## Why these choices

- Keep setup separate from coaching: no unvalidated recommendation is exposed.
- Use Groq structured responses and Pydantic for typed responses; require a rationale for every
  recommendation in Stage 2. A lower temperature alone does not make advice safe.
- Use pandas and Plotly for evaluation tables and charts. requests sends Groq API
  calls through its OpenAI-compatible HTTPS interface.
- No image support or Pillow dependency is needed for this CoachBot scenario.
- Pin direct dependencies for repeatable setup; this is not a complete transitive
  lockfile. Installation and pip's dependency consistency check passed on Python 3.13.
- Configuration includes future sweep/cache defaults, but those features are not
  implemented yet. The full grid is 18 configurations per applicable prompt/case.
- Cache, raw responses and feedback are ignored by Git. Only reviewed anonymized
  evidence belongs in docs/evidence. Cloud-local files are not durable storage;
  later feedback/evaluation features must provide downloads or persistent storage.

## Later submission requirements retained

Stage 6: max_tokens sweep, subset, caching, sleep, resumable logs, exact call
estimate and a non-English case. Stage 7: README and unscored five-criterion
rubric. Stage 7.5: six numbered evidence screenshots with README locations.
Stage 8: honest rubric audit. Stage 9: cover template and PDF export, collaborator
access for ai.assignments@wacpinternational.org, and logged-out access checks.
Student-authored prompts, research, findings, reflections and scores stay yours.

## Technical references

Verification: Python syntax and TOML parsing passed. Streamlit's test runner
passed the setup screen, English default, placeholder-key handling, simulated
model listing, and simulated 429/403/500 error fallbacks. No real API key or
generation call was used. Live model access, browser appearance and Cloud
deployment have not been verified.

- [Groq models](https://console.groq.com/docs/models)
- [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs)
- [Streamlit secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- Dependency pins were checked against each package's official PyPI JSON metadata
  on October 30, 2026. They are setup choices, not student research findings.
