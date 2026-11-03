# CoachBot AI — Stage 4

Implemented `core/safety.py` and `core/formatter.py`. These modules validate inputs,
inject constraints, screen outputs, and create typed display cards and Markdown
exports. They are engineering guardrails, not clinical validation or medical care.
The Streamlit coaching interface is still scheduled for Stage 5.

## Input checks before generation

`prepare_request()` takes a registry entry, its input values and an explicit
`HealthContext`. The health controls must ask about injury status, affected areas,
current pain, suspected concussion and urgent symptoms. They must not silently
default to a declaration that the user is healthy.

| Input condition | App behavior |
|---|---|
| Reported urgent symptoms | Fixed urgent-help notice; no API call |
| Suspected concussion | Fixed medical-assessment notice; no API call |
| Current pain | Fixed pause/referral notice; no API call |
| Unknown injury context | Clarification notice; no API call |
| Conflicting injury answers | Clarification notice; no API call |
| Listed English danger/head-injury terms | Conservative local referral; no API call |
| Recognized instruction override | Local request-rewrite notice; no API call |
| Missing/extra/invalid fields | Local validation notice; no API call |
| Complete inputs without a listed blocking condition | Build the constrained request |

Every local recommendation includes a short rationale. The application does not
diagnose the user or decide that they have recovered. Historical or negated
references can cause conservative referrals because text matching cannot establish
whether a condition is current.

This youth prototype accepts integer ages 1–17. That is an input range, not proof
that the feature is suitable for every age. For under-13 inputs the prompt requires
short, concrete language and parent/trusted-adult involvement. A real deployment
still needs an agreed audience and appropriate supervision; no date of birth is
collected by these modules.

Future student-authored features must include `age` and `injury_context` slots.
With injury_status `none`, the current interface integration should use a canonical
description such as `none` or `no injuries`; contradictory free text is rejected.
The form labels remain English. Other input fields can contain Unicode text.

## Injury restrictions and age-appropriate output

The trusted system constraints prohibit diagnosis, medication and supplement
prescriptions, restrictive diets, weight-loss targets, training through pain,
shaming, secrecy and promises of safety. Injury history restricts output to
nonphysical discussion, even if the user claims to have recovered.

Selected affected areas add explicit exclusions. For example, knee and shoulder
selections both contribute restrictions to the same request. These broad product
exclusions are not a medically complete contraindication table. An unspecified
injury location still excludes all physical exercise prescriptions.

The existing `tactical_reflection` example is always discussion-only and allows
at most three suggestions. The input guard does not author additional prompts.

## Output screening

`screen_output()` revalidates the schema and checks titles, actions, rationales
and follow-up questions. It looks for listed unsafe claims, hostile wording,
instruction overrides, active HTML, out-of-scope physical suggestions, invalid
visible text, mismatched language labels and too many reflection suggestions.
An English sentence-length rule adds a rough readability check; it is not a
reading-age assessment.

If a rule matches, the entire response is withheld. The replacement is a fixed
local referral with its own rationale. No rejected suggestion is copied into
the replacement. Both cached and fresh responses go through the same screening.

**Limits:** these checks use a bounded English pattern list. They can miss
paraphrases, contextual risks, novel instructions and unsafe non-English text.
They can also reject benign or negated phrases. A `screened` display state means
only that no listed rule matched; it must never be labeled “medically safe” or
“approved.” Human review remains necessary.

## Formatting and exports

`format_result()` returns a `DisplayPlan` containing typed `SuggestionCard`
objects, clarification questions, a disclaimer, a review note and the source.
Every card has `title`, `action` and `rationale`. Raw responses and private
attempt logs are never display inputs.

Stage 5 widgets must render the action and then the rationale directly beneath
it, and keep the disclaimer and review note visible on every view. They should
use plain-text widgets for generated strings rather than enabling unsafe HTML.
The setup screen already retains the coach/physician disclaimer.

`to_markdown()` exports the same reviewed cards with the rationale below each
action. It escapes Markdown links and HTML, preserves readable Unicode, removes
hidden controls and includes the disclaimer even for empty/error views. It makes
no extra API calls.

English remains the default AI response language. An explicit language selection
is passed through unchanged. Fixed application safety notices remain in English
and are labeled as application notices, not AI translations. Non-English AI
responses include a visible note that pattern screening is mainly English.

## Integration order for Stage 5

The following fragment assumes that `entry`, `values` and `health` have been
collected by the UI. It is not a new student prompt:

```python
from core.safety import prepare_request
from core.formatter import format_result, to_markdown
from core.groq_client import GroqClient, SetupError
from core.schemas import GenerationResult

preflight = prepare_request(entry, values, health, language=selected_language)
result = None
if preflight.may_generate:
    try:
        with GroqClient.from_streamlit() as client:
            result = client.generate(preflight.request)
    except SetupError:
        result = GenerationResult(
            status="configuration_error", message="Complete the private API setup."
        )

view = format_result(preflight, result)
download_text = to_markdown(view)
```

Never call the model when `preflight.may_generate` is false. Never render
`result.data` directly or export a raw model response. `system_constraints` are
constructed by trusted code rather than taken from a user-editable system field.
The injected safety-policy version participates in the existing cache key;
display screening is repeated even on a cache hit.

## Verification

**72 offline tests passed:** the existing 40 tests plus 32 Stage 4 tests.
Coverage includes multiple injuries, conflicting inputs, urgent/pain flags,
missing fields, instruction overrides, unsafe content in rationale/questions,
hostile tone, cache screening, partial-output rejection, Markdown escaping,
Unicode, fixed notices and the preflight → fake client → formatter path.
The blocked-input integration test makes zero calls to its fake client.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

No live Groq requests were made. These synthetic engineering checks do not
replace the student's evaluation cases, research, quality scores or findings.
Live model quality, browser rendering and multilingual safety are unverified.

## Engineering reference notes

The fixed concussion referral follows the principle that suspected concussion
requires removal from sport and healthcare assessment, rather than AI clearance.
See [CDC: responding to a sports-related concussion](https://www.cdc.gov/heads-up/response/index.html).
The limited danger-term list is informed by [CDC: concussion signs and symptoms](https://www.cdc.gov/heads-up/signs-symptoms/index.html).
The pain notice follows the instruction to stop activity that hurts in
[AAP/HealthyChildren: sports injury prevention](https://www.healthychildren.org/English/health-issues/injuries-emergencies/sports-injuries/Pages/Sports-Injuries-Treatment.aspx).

These references document engineering choices only. Your graded research findings
and literature discussion remain [MY INPUT NEEDED].
