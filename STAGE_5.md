# CoachBot AI — Stage 5

The Streamlit interface now connects the existing prompt, safety, Groq client
and output formatter. English remains the default response language. Interface
labels and fixed application safety notices remain English; the selected AI
response language travels separately from the English schema keys.

## What is included

- A single-column form with retained session inputs, explicit unanswered health
  controls, a language selector and temperature, top_p and output-token settings.
- A fictional sample button that fills the current tactical-reflection form for
  exploration; it makes no model request until the user submits the form.
- A loading indicator while checking inputs and preparing a response.
- Local clarification/referral messages before any model request where required.
- Reviewed suggestion cards with a rationale directly below every action.
- Markdown plan downloads containing the rationale, disclaimer and review note.
- Thumbs-up/down feedback for screened model responses, saved as JSONL with a
  downloadable session copy. Voting and downloading do not regenerate a response.
- Changed inputs hide the previous result and its export until resubmission.

Only the existing tactical-reflection example is active. The other nine prompt
slots remain student-owned placeholders in `docs/PROMPT_AUTHORING.md`.

## Run locally

From the project folder, after completing the environment setup in `STAGE_1.md`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

`config.MODEL_NAME` defaults to `openai/gpt-oss-20b` and no API key is supplied.
Follow the Stage 1 private setup instructions before using real AI generation. Do not put
credentials in the form, screenshots, source code or submitted archive.

## Session and feedback behavior

Inputs and the latest displayed result persist through normal Streamlit reruns
within the browser session. Refreshing into a new session or restarting the
server may clear them. Public feature labels use `st.cache_data`; private inputs
and displayed results use session state. The client maintains its existing
private response-cache namespace and screens cached output again before display.

Feedback files live at `data/feedback/<session-id>/feedback.jsonl`. Events contain
random event/response IDs, prompt ID/version, vote and timestamp. They do not
contain the user's sporting or injury text. Repeated reruns do not duplicate an
unchanged vote; changed votes create new events. If local writing fails, the
session copy remains downloadable. Cloud-local files are not durable storage and
may disappear after a restart. Download required evidence before ending a session.

## Verification and evidence

**86 offline tests passed**, including 14 Stage 5 tests using Streamlit AppTest.
They cover default English, explicitly unanswered health controls, incomplete
inputs, priority local referral, missing setup, mocked successful rendering,
retained inputs, stale-result hiding, Tamil/native-script language selection,
cached-output screening, feedback deduplication, storage failure and isolation.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The real local browser was inspected at **375 × 812 pixels**. The measured page
width was 375 pixels, with no horizontal page overflow. A synthetic urgent-symptom
selection produced the local referral and its rationale without a Groq call.
The actual Markdown download was opened and checked for the action, rationale,
disclaimer and review note.

1. [Mobile interface](docs/evidence/stage5-mobile-375.jpg)
2. [Mobile edge-case response with rationale](docs/evidence/stage5-mobile-edge-case.jpg)

These are engineering evidence screenshots, not student-written evaluation
findings. The final README evidence placement checklist is reserved for Stage 7.5.

No live Groq request or cloud deployment was tested. Successful AI response and
feedback flows were tested with synthetic responses. Language selection and
schema parsing tests do not establish real translation quality or multilingual
safety. Existing English-pattern safety limitations remain documented in Stage 4.
Student scores, findings, research and reflection remain [MY INPUT NEEDED].

Stage 5 ends here; Stage 6 has not been started.
