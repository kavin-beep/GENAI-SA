# CoachBot AI — Stage 3

The versioned prompt registry is implemented in `core/prompts.py`. There is
**exactly one registered feature and one real version**: `tactical_reflection` v1.
The other nine remain yours to author in `docs/PROMPT_AUTHORING.md`.

## What each entry stores

| Field | Purpose |
|---|---|
| `id` | Stable feature identifier, such as `tactical_reflection` |
| `version` | Explicit snapshot: v1, v2, v3, and so on |
| `intent` | What the feature is meant to do |
| `template` | Instruction text containing plain `{named_slots}` |
| `required_inputs` | Exact names of the slots the template needs |
| `recommended_temperature` | Initial sampling setting; not an observed optimum |
| `recommended_top_p` | Initial diversity setting; not a safety guarantee |
| `output_schema` | `CoachingResponse`, with required rationale per recommendation |
| `changelog` | Versioned descriptions of actual edits |

Entries and change notes are immutable while the program runs. Registration
revalidates definitions and refuses an existing ID/version, so edits require a
new version. Preserve the old definitions in source control as well.

## The one worked example

`TACTICAL_REFLECTION_V1` reviews an athlete's described decision and asks for
discussion or communication suggestions, each with a rationale. Its inputs are:

- sport
- position
- age
- region
- situation
- available_resources
- injury_context
- goal

The example does not choose your region or sport for you. It avoids physical
training prescriptions and asks for clarification or professional referral when
needed. Its temperature 0.2 and top_p 0.8 are starting settings, not tested quality
claims. Stage 4 still needs to implement domain validation and content screening.

## Inspect the registry without an API key

Run from the project folder using your installed environment:

```powershell
.\.venv\Scripts\python.exe -c "from core.prompts import REGISTRY; print([(p.id, p.version) for p in REGISTRY.entries()])"
```

Expected output:

```text
[('tactical_reflection', 'v1')]
```

## Connecting it to the later interface

This integration fragment assumes `validated_inputs` and `trusted_constraints`
come from the Stage 4 safety layer. It constructs a request; the current Groq client sends it later:

```python
from core.prompts import REGISTRY

entry = REGISTRY.get("tactical_reflection", version="v1")
request = entry.build_request(
    validated_inputs,
    system_constraints=trusted_constraints,
)
# request.language is English unless the caller explicitly supplies language=...
```

The UI will send the resulting `GenerationRequest` through the existing client.
`system_constraints` is trusted application code, never a free-text user field.
For an explicit language selection, pass `language="Tamil"`, for example. The
client controls response language centrally and keeps schema keys in English.

To evaluate different settings, pass a `GenerationParameters` object as
`parameters=`. It overrides the entry's recommended temperature and top_p and
lets the evaluator sweep max_tokens. A missing override uses the entry defaults
and the shared configured output limit.

## Adding and revising your own entries

1. Draft your intent, template, slot names and starting parameters in the authoring
   worksheet. Use your research and intended users to make these choices.
2. Create a complete `PromptSpec` in `core/prompts.py`, using the one example's
   structure and your own content. Keep `output_schema=CoachingResponse`.
3. Add `REGISTRY.register(your_entry)` after its definition. Incomplete placeholder
   templates and intents are rejected rather than counted as working features.
4. For a revision, retain v1, create a new entry with the same ID and version v2,
   preserve earlier change notes, and append a note describing your actual edit.
5. Run the offline tests. Later, compare responses and write your own findings.

Use `REGISTRY.get(id, version="v1")` to reproduce a pinned version.
`REGISTRY.get(id)` chooses the highest numeric version (v10 sorts after v2).
`REGISTRY.entries()` returns one current version per distinct feature.
`REGISTRY.entries(all_versions=True)` returns every saved version for comparison.
Ten versions of one feature do not satisfy ten distinct prompt/features.

No v2/v3 coaching content or claims of improvement have been authored for you.
Tests use identical-template version fixtures solely to check registry behavior.

## Validation and limitations

The renderer rejects missing, extra, blank, non-text and oversized input values.
Template slots must match `required_inputs`; attribute access, indexing,
conversions and formatting specifications are rejected. Values are JSON-quoted
and inserted once, so braces or newlines inside an input cannot become template
fields or extra unquoted input lines.

Quoting is not a complete defense against prompt injection. Semantic checks
(including age, injuries and conflicting instructions) remain Stage 4 work.
The registry binds every entry to the client's existing response contract, rather
than accepting a schema the client would silently ignore.

## Verification

All **40 offline tests passed**: 26 Stage 2 tests plus 14 registry tests. These cover
the English default, explicit language and parameter overrides, numeric version
selection, retained snapshots, duplicate rejection, malformed slots, Unicode input,
quoting, immutability and definition validation. No API call was made, and no
generated coaching response or student evaluation finding is claimed.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Stage 3 ends here. Stage 4 will add safety rules and formatting. The final coaching
interface remains scheduled for Stage 5.
