# Stage 7.5 — Screenshot evidence checklist

Capture real screens from your own project. This is a capture plan, not evidence
that API access, live generation, deployment or evaluation has been completed.
Keep your captions and findings in your own words. Use fictional/anonymized inputs.
Save only reviewed screenshots in `docs/evidence/`; never include an API key,
private health details, raw response logs or private account information.

## 1. API key generation in the Groq Console

- [ ] Capture the Groq Console key-generation confirmation or resulting key entry.
- [ ] Show enough page context to identify Groq Console and the completed action.
- [ ] Cover the **entire key** with a solid opaque rectangle; also remove any
  copied-key tooltip, unrelated account information and sensitive project details.
  Export a flattened image and reopen it to verify redaction. Do not commit the
  unredacted original. If a key has already been exposed, replace it privately.
- **File:** `docs/evidence/01-groq-key-redacted.png`
- **Exact README location:** [Local setup → API setup evidence](../README.md#api-setup-evidence),
  directly below that heading, replacing the screenshot placeholder.
- **Caption to complete:** [MY INPUT NEEDED: date, action shown, and confirmation
  that the key is fully redacted. Do not claim this proves generation quota.]
- **Current status:** not captured.

Paste this after the actual image exists:

```markdown
![Groq API key generation with the entire key redacted](docs/evidence/01-groq-key-redacted.png)
```

## 2. Local app running

- [ ] Start the root `app.py` locally and capture the CoachBot title with a visible
  localhost address, relevant form context and the app's result area.
- [ ] Prefer a completed live response after private setup, showing the selected
  language, action, rationale and disclaimer. A local-only check or setup screen
  may demonstrate execution but must be labeled accurately; it is not proof of
  working Groq generation.
- [ ] If the long form and result cannot fit legibly, add a second local screenshot
  instead of shrinking the entire page until the text is unreadable.
- **File:** `docs/evidence/02-local-app.png` (optional companion `02-local-result.png`).
- **Exact README location:** [Local setup → Local execution evidence](../README.md#local-execution-evidence),
  directly below that heading, replacing the screenshot placeholder.
- **Caption to complete:** [MY INPUT NEEDED: date, input case, model if used,
  whether the result is live/cached/local, and the flow demonstrated.]
- **Current status:** the dedicated desktop/local capture is still needed.

```markdown
![CoachBot AI running locally](docs/evidence/02-local-app.png)
```

## 3. Deployed app on Streamlit Cloud

- [ ] Deploy the repository's `app.py` and capture the running app with its actual
  public address visible. A deployment dashboard alone is insufficient.
- [ ] Show the app title and a usable flow/result. Keep secrets settings closed.
- [ ] Open the deployed URL in a logged-out/private browser and record the actual
  access result; fix access issues before claiming public availability.
- **File:** `docs/evidence/03-streamlit-cloud.png`
- **Exact README location:** [Deployment → Deployed app evidence](../README.md#deployed-app-evidence),
  directly below that heading, replacing the screenshot placeholder. Fill the
  deployed URL and deployment record elsewhere in the README separately.
- **Caption to complete:** [MY INPUT NEEDED: URL, date, deployed commit, actual
  test performed, whether AI generation succeeded, and logged-out access result.]
- **Current status:** deployment and screenshot pending.

```markdown
![CoachBot AI running on Streamlit Community Cloud](docs/evidence/03-streamlit-cloud.png)
```

## 4. App handling an edge case

- [ ] Use a synthetic case such as the bundled urgent-symptom flag, contradictory
  injury answers or empty input. Capture the triggered condition and resulting
  clarification/referral, including its rationale and disclaimer.
- [ ] If the input and result need separate views, label both with the same case ID.
- [ ] Label a local safety notice as an application response, not an AI-generated
  answer. A screenshot alone does not prove zero API calls; use the engineering
  test/log evidence for that claim.
- **Existing file:** `docs/evidence/stage5-mobile-edge-case.jpg`
- **Exact README location:** [Demo evidence → Edge-case evidence](../README.md#edge-case-evidence),
  where the existing engineering screenshot is already embedded.
- **Caption to complete:** [MY INPUT NEEDED: synthetic case, condition selected,
  behavior actually observed, date and evidence limitations.]
- **Current status:** an existing Stage 5 capture shows the local urgent-help
  response and rationale. It does not show the entire input form or establish
  live Groq behavior. Review it and add an input-view companion if needed.

Existing embed (do not duplicate):

```markdown
![Stage 5 local edge-case notice](docs/evidence/stage5-mobile-edge-case.jpg)
```

## 5. Mobile-width view

- [ ] Set the viewport to **375px wide**, record its height, and capture legible
  controls. Also inspect the result cards, rationale and download control.
- [ ] Check for clipping, horizontal scrolling and inaccessible controls across
  the form and result. Record what you actually checked; a narrow screenshot
  alone does not establish compatibility with all phones or assistive technology.
- **Existing file:** `docs/evidence/stage5-mobile-375.jpg`
- **Exact README location:** [Demo evidence → Mobile-width evidence](../README.md#mobile-width-evidence),
  where the existing mobile engineering capture is already embedded. A result
  companion can follow it; the existing edge-case capture is also 375px wide.
- **Caption to complete:** [MY INPUT NEEDED: browser/device, 375 × height viewport,
  date, checked flows and actual observations.]
- **Current status:** Stage 5 captured a **375 × 812** view and measured page width
  at 375px. Your own review/caption and any further-device checks remain pending.

Existing embed (do not duplicate):

```markdown
![Stage 5 local mobile interface](docs/evidence/stage5-mobile-375.jpg)
```

## 6. Evaluation results table

- [ ] After a deliberate real evaluation, open the reviewed `tuning.csv` or
  `summary.csv` as a readable table and capture the relevant rows/columns.
- [ ] Show temperature, top_p, **max_tokens**, output length/token counts and
  structural completeness/truncation. Include prompt/version and case or grouped
  sample context; split wide tables across clearly labeled images if necessary.
- [ ] Distinguish first response from repair, cached data from new calls, local
  notices from model responses, and partial from completed sweeps.
- [ ] Keep raw response text and personal inputs out of the image. Never invent
  values or use mocked test outputs as if they were measured Groq results.
- **File:** `docs/evidence/06-evaluation-table.png`
- **Exact README location:** [Testing and parameter tuning → Evaluation table and evidence](../README.md#evaluation-table-and-evidence),
  directly after your populated tuning table and before **Optimization findings**.
- **Caption to complete:** [MY INPUT NEEDED: run date, model, prompts/versions,
  cases/sample count, parameter range, cache status and unfinished/failed jobs.]
- **Current status:** no live evaluation table or screenshot exists. Run the
  [zero-call plan first](../STAGE_6.md), check the budget, then execute deliberately
  after private setup. Synthetic cases are acceptable engineering fixtures but
  must be labeled as such; they do not supply your evaluation conclusions.

```markdown
![Reviewed parameter sweep results including output-token limits](docs/evidence/06-evaluation-table.png)
```

## Final evidence review

- [ ] All six required evidence categories are covered by real images.
- [ ] Every image is legible, correctly captioned and embedded at the location above.
- [ ] Image links work in the GitHub README and deployed/repository URLs work.
- [ ] Screenshots contain no keys or private personal context.
- [ ] Captions distinguish engineering checks, live model responses and local notices.
- [ ] All dates, outputs, scores and observations reflect what actually happened.

Existing screenshots may be reused with honest attribution. The numbered file
names are suggestions for new captures, not reasons to rename existing evidence.
This plan does not fill student findings or quality scores. Stage 8's rubric audit
and Stage 9's submission document remain separate stages.
