# Stage 8 — Pre-submission rubric audit

**Audit date:** 3 November 2026.  
**Decision:** not ready for submission. The engineering foundation is implemented;
student authorship, live model evidence and publication remain incomplete.

This is an engineering and evidence audit, not your output-quality checklist,
reflection, research findings or an examiner's mark. Those student-owned sections
remain blank. No numerical score or guaranteed grade is assigned.

## Basis and verification limits

Rubric source: the supplied `YEAR_1_Generative A.I_Summative_Assessment(2).docx`,
CoachBot Task 2 and Appendix A. The five criterion weights are 10 + 15 + 10 + 10 +
15 = **60 marks**. Its band headings use generic 10/8/6/4 labels even on 15-mark
criteria; this audit uses the explicit criterion weights and descriptive evidence
requirements, without inventing a conversion.

The brief is assessed as source material. The user's staged protocol, modern SDK
requirement, English default and student-authorship boundaries govern this build.
No ArtRestorer image requirements are applied to CoachBot.

Current files were inspected: README, registry, configuration, UI, dependencies,
evidence directory and evaluation output directory. The existing Stage 6 test log
records **98 offline tests passed**. Tests were not rerun for this document-only
audit. The Stage 5 notes/screenshots record a local 375px check and Markdown
export; this is prior engineering evidence, not a new browser verification.

At the time of the Stage 8 audit, `MODEL_NAME` was blank and no project-local
secrets file existed. The model default was added later during local UI work. Secrets
contents were not inspected. No live evaluation files are present under `eval/results/` beyond
`.gitkeep`. The README's GitHub and deployed URLs remain placeholders; this project
folder has no `.git` metadata. These facts establish missing evidence here, not
that no repository could exist elsewhere. No external repository/account search,
live Groq request or deployment was performed.

## Criterion 1 — Problem Understanding & Solution Design (10 marks)

**Rubric expectation:** a clear real-world problem, mapped user needs and a
solution whose intended impact follows from that understanding.

**Present:** a modular architecture, sports/context/health inputs, explicit English
default, rationale-bearing outputs and a README structure for needs and research.

**Missing:** the student's problem statement, specific intended audience/persona,
research findings with citations, objectives, success criteria and need-to-feature
mapping. The fixture's football/India context is synthetic and cannot be treated
as research about real users. An input age range is not a defined user persona.

**Scope mismatch:** the brief describes workout, recovery, tactical and nutrition
support, including training/nutrition preferences. The current active feature is
only discussion-based tactical reflection, and those additional preference inputs
and features are absent. Safe restrictions are implemented, but they do not by
themselves demonstrate that the intended brief has been fulfilled.

**Standing:** architecture evidence exists; the core student problem/research
justification and scope alignment are not demonstrated.

**To close:** [MY INPUT NEEDED: write the README Problem and intended users and
Research findings sections from your own research; define the intended scope and
resolve its differences from the brief with your teacher. Record the actual
agreement rather than claiming approval that has not occurred.]

## Criterion 2 — Prompt Engineering, Feature Design & Creativity (15 marks)

**Rubric expectation:** ten diverse, user-focused prompts/features, with meaningful
design rather than repeated versions of the same feature.

**Present:** `PromptSpec`, named inputs, immutable version snapshots, changelogs,
English schema keys and one worked `tactical_reflection` v1 engineering example.
The authoring worksheet contains nine empty slots. The selected language is
carried through the client while recommendations require rationales.

**Missing:** nine student-authored prompts and their working integration, feature
coverage, design justification and actual revision evidence. Only one v1 is
registered; support for versioning is not proof that refinement has happened.
The supplied example should be disclosed as engineering assistance, not passed
off as independently authored student work.

**Standing:** registry infrastructure is implemented; the ten-prompt criterion is
not met. A polished single feature cannot substitute for the missing features.

**To close:** [MY INPUT NEEDED: author the remaining entries in
`docs/PROMPT_AUTHORING.md`, map them to your users, register/test them, and record
real prompt changes with before/after evidence.]

**Integration follow-up:** when additional prompts are registered, revisit the
hardcoded tactical-reflection caption in `ui/components.py` and the app's opening
copy. They currently describe the only active feature correctly, but would be
misleading if reused unchanged for different features. New fields, safety scope,
case coverage and result rendering need review for each authored feature; simply
adding nine IDs does not complete integration.

## Criterion 3 — Output Quality & Response Relevance (10 marks)

**Rubric expectation:** coherent, informative, position-sensitive responses that
fit the athlete's supplied context.

**Present:** strict schema validation; a rationale per recommendation; input checks;
limited output screening; rejected/partial response withholding; a common display
and Markdown-export path. Offline tests exercise valid/invalid responses and
language labels. An unscored five-criterion quality rubric is supplied.

**Missing:** real model responses, student quality judgments with evidence,
position/region relevance assessment, actual feedback, and independent assessment
of non-English response quality. Thumbs capture is implemented, but that does not
show anyone has reviewed outputs. A fixed local referral is not a model response.

**Standing:** formatting and failure-handling are supported by offline evidence;
actual model response quality is unproven. A valid JSON shape or normal finish
reason does not demonstrate relevance, factual correctness or safety.

**To close:** [MY INPUT NEEDED: configure the model, collect anonymized actual
responses for your cases, complete the rubric yourself, and record the sources or
real reviewer feedback used to assess them. Include limitations and unsuccessful
outputs; do not invent a reviewer or conclusions.]

**Safety limitation:** English pattern matching can miss non-English or contextual
risks and reject benign phrases. The selected language label does not verify that
the prose is translated correctly. Do not claim universal multilingual safety,
medical clearance or guaranteed age suitability.

## Criterion 4 — Model Testing, Tuning & Optimization (10 marks)

**Rubric expectation:** actual tuning across parameters, prompt refinement and
error handling supported by logs and comparisons.

**Present:** a temperature/top_p/max_tokens sweep; subset planning; stable response
caching; bounded calls and sleep; atomic checkpoints and failure receipts;
resumption; per-job CSV/JSONL and grouped tuning summaries; synthetic edge cases
including Tamil. The notebook imports core logic. The prior 98-test pass includes
12 harness integration tests for budgets, cache reuse, rate limits and metrics.

**Missing:** a selected model, actual parameter-run logs, a real results table,
student interpretation of trade-offs, evidence-based settings and measured prompt
improvements. `eval/results/` contains no run artifacts. There is no evidence of
live quota or current provider compatibility.

**Standing:** the evaluation mechanism and offline failure handling are implemented;
empirical model tuning and optimization have not been demonstrated.

**To close:** [MY INPUT NEEDED: supply your anonymized cases, run a budgeted live
subset, inspect length/completeness alongside quality, extend only as needed, then
write your own tuning findings and actual prompt revisions.]

**Budget reminder:** the bundled eight-case/one-prompt grid plans 144 jobs: 90 local
checks and 54 model-eligible jobs. At first-attempt success, expect 54 uncached
calls; the retry/repair ceiling is 324 before the per-invocation cap. The default
cap is 12. A three-job subset normally needs three calls but retries may consume
its cap earlier. Counts change as features/cases change: rerun the zero-call plan.
Do not describe the planned count as observed usage. A single cached sample per
configuration is not statistical proof of superiority.

## Criterion 5 — Web App Deployment, Usability & GitHub Repository (15 marks)

**Rubric expectation:** a functional deployed Streamlit application, responsive
usable interface and accessible, well-documented GitHub repository.

**Present:** root `app.py`; pinned dependencies; setup templates; friendly missing
setup handling; retained session inputs; loading indicator; rationale cards;
Markdown download; feedback JSONL; a README skeleton; notebook and script links.
Two Stage 5 captures support local mobile/edge-case engineering checks.

**Missing:** verified GitHub URL/repository access, public Cloud URL, hosted
secrets/model setup, live hosted functional testing, redacted key-generation
capture, dedicated local execution evidence, deployment capture and evaluation
table screenshot. The README is deliberately unfinished. The existence of a ZIP
is not evidence that a public repository or deployment works.

**Standing:** local interface engineering is demonstrated; the required deployed
and accessible submission is not demonstrated.

**To close:** configure and verify the real model locally, publish the intended
project files at repository root, configure private hosted secrets, deploy and
verify the actual app and repository links from a logged-out browser. Complete
[the six-item evidence checklist](EVIDENCE_PLAN.md). Record actual tests and access
results in the README. Do not publish raw/private evaluation artifacts.

## Submission-layer requirements audit

| Requirement | Current evidence | Remaining action |
|---|---|---|
| Six screenshot categories | Numbered plan; existing mobile and edge-case images | Capture the other four categories; review/caption all six |
| Cover page and PDF | User-edited cover draft exists in chat | Stage 9 artifact/PDF; fill required personal fields yourself |
| Repo collaborator and access | Reminder only | Provide access for ai.assignments@wacpinternational.org and verify it; check logged-out repository access |
| Sweep max_tokens and summarize length/completeness | Runner and tested metrics | Real runs, reviewed table and student interpretation |
| Quota guard: subset/cache/sleep/resume/count | Implemented; offline tests recorded | Use actual account settings and budget; retain outputs |
| Rationale per recommendation | Required schema field; displayed/exported | Verify live responses and future features |
| Language selector, English keys, non-English eval case | Implemented; synthetic Tamil case | Real translation/relevance assessment; do not claim every language works |
| Five-criterion quality checklist | Unscored rubric supplied | Student scores, evidence and findings |
| Pinned named dependencies | Current requirements: streamlit, requests, pandas, plotly, pydantic | Verify fresh/hosted installation; Groq is called over HTTPS through requests; no Pillow needed for text-only CoachBot |
| Legacy SDK note | requirements.txt records 2025-11-30 end of support | Keep accurate terminology: SDK support sunset is not a universal runtime shutdown |
| Notebook companion | Connectivity/sweep/schema demos importing core; offline cells checked | Deliberate live connectivity if needed; student notes; avoid saved private outputs |
| ArtRestorer image ambiguity | Not applicable to selected CoachBot scenario | No image upload feature required for this selected scope |

## Prioritized completion order

1. **Resolve scope and author the missing material.** Define the intended users,
   research-backed objectives and final feature coverage; author the nine prompts.
   These are submission blockers that infrastructure cannot replace.
2. **Complete model setup and a small live smoke test.** Select a served model,
   configure the key privately, verify one relevant structured response and failure
   handling. Never put the key into this audit or the README.
3. **Integrate and evaluate the actual feature set.** Update feature-specific UI
   copy where needed, add cases for every registered prompt and run bounded sweeps.
   Retain real evidence; write your own judgments and revisions.
4. **Publish and verify.** Complete the README, deploy, check hosted behavior and
   logged-out access, provide required collaborator access and finish screenshots.
5. **Create the Stage 9 submission document.** Use the current user-edited cover
   draft, fill the required fields, verify links, export/check the PDF, then revisit
   this audit against the finished artifacts.

## Claims supported versus unsupported

Supported: a modular prototype exists; one example feature is registered; outputs
require rationales; an evaluation runner and notebook exist; 98 offline tests
passed in the recorded Stage 6 run; two local engineering screenshots exist.

Unsupported: ten authored working features; established real-user impact; proven
coaching/medical safety; high-quality multilingual responses; optimized model
settings; completed live evaluation; successful Cloud deployment; verified public
repository access; a final grade or submission-ready project.

This audit is complete. It deliberately does not fill student research, findings,
quality scores, reflection or the nine prompts. Stage 9 is not started.
