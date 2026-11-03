"""Offline registry tests; version fixtures do not author new coaching prompts."""

import unittest

from pydantic import ValidationError

from core.prompts import ChangeNote, PromptRegistry, PromptSpec, REGISTRY, TACTICAL_REFLECTION_V1
from core.schemas import CoachingResponse, GenerationParameters


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.example = TACTICAL_REFLECTION_V1
        self.values = {name: "Synthetic test value" for name in self.example.required_inputs}

    def definition(self, **changes):
        values = self.example.model_dump()
        values.update(changes)
        return PromptSpec.model_validate(values)

    def test_exactly_one_feature_and_one_version(self):
        self.assertEqual(len(REGISTRY.entries()), 1)
        self.assertEqual(len(REGISTRY.entries(all_versions=True)), 1)
        self.assertEqual(REGISTRY.versions(self.example.id), ("v1",))

    def test_example_builds_english_request_with_rationale_schema(self):
        request = self.example.build_request(self.values)
        self.assertEqual(request.language, "English")
        self.assertEqual(request.prompt_id, "tactical_reflection")
        self.assertEqual(request.prompt_version, "v1")
        self.assertEqual(request.parameters.temperature, 0.2)
        self.assertEqual(request.parameters.top_p, 0.8)
        self.assertIs(self.example.output_schema, CoachingResponse)
        self.assertIn("rationale", request.prompt)

    def test_explicit_language_and_eval_params(self):
        params = GenerationParameters(temperature=0.9, top_p=0.95, max_tokens=256)
        request = self.example.build_request(self.values, language="Tamil", parameters=params, system_constraints="Trusted test constraint")
        self.assertEqual(request.language, "Tamil")
        self.assertEqual(request.parameters, params)
        self.assertEqual(request.system_constraints, "Trusted test constraint")

    def test_missing_extra_empty_nontext_and_oversized_inputs(self):
        missing = dict(self.values)
        missing.pop("sport")
        for values in (missing, {**self.values, "extra": "x"}, {**self.values, "sport": " "},
                       {**self.values, "sport": 12}, {**self.values, "sport": "x" * 2001}):
            with self.subTest(values=list(values)):
                with self.assertRaises(ValueError):
                    self.example.render(values)

    def test_braces_quotes_and_newlines_stay_data(self):
        self.values["sport"] = 'A "quote"\n{position} {x.__class__}'
        rendered = self.example.render(self.values)
        self.assertIn('Sport: "A \\"quote\\"\\n{position} {x.__class__}"', rendered)

    def test_unicode_preserved(self):
        self.values["region"] = "தமிழ்நாடு"
        self.assertIn("தமிழ்நாடு", self.example.render(self.values))

    def test_duplicate_registration_is_rejected(self):
        registry = PromptRegistry()
        registry.register(self.example)
        with self.assertRaises(ValueError):
            registry.register(self.example)

    def test_versions_are_numeric_and_old_snapshots_remain(self):
        registry = PromptRegistry()
        registry.register(self.example)
        # Identical template: these are version-order fixtures, not authored revisions.
        for version in ("v10", "v2", "v3"):
            entry = self.definition(version=version, changelog=(
                self.example.changelog[0], ChangeNote(version=version, change="Synthetic version-order test only."),
            ))
            registry.register(entry)
        self.assertEqual(registry.versions(self.example.id), ("v1", "v2", "v3", "v10"))
        self.assertEqual(registry.get(self.example.id).version, "v10")
        self.assertEqual(registry.get(self.example.id, "v1"), self.example)
        self.assertEqual(len(registry.entries()), 1)
        self.assertEqual(len(registry.entries(all_versions=True)), 4)

    def test_unknown_id_and_version(self):
        for prompt_id, version in (("missing", None), (self.example.id, "v99")):
            with self.assertRaises(KeyError):
                REGISTRY.get(prompt_id, version)

    def test_immutable_definition_and_changelog(self):
        with self.assertRaises(ValidationError):
            self.example.template = "replace"
        with self.assertRaises(ValidationError):
            self.example.changelog[0].change = "replace"

    def test_template_rejects_traversal_conversions_specs_and_mismatch(self):
        for template in ("{sport.__class__}", "{sport[0]}", "{sport!r}", "{sport:>20}", "{}", "{other}", "{sport"):
            with self.subTest(template=template):
                with self.assertRaises(ValidationError):
                    self.definition(template=template, required_inputs=("sport",))

    def test_duplicate_inputs_and_placeholder_definition_rejected(self):
        for changes in ({"required_inputs": ("sport", "sport")}, {"intent": "[MY INPUT NEEDED]"},
                        {"template": "[MY INPUT NEEDED: write template]"}):
            with self.assertRaises(ValidationError):
                self.definition(**changes)

    def test_changelog_must_end_at_version_and_increase(self):
        for changes in (
            {"version": "v2"},
            {"changelog": (self.example.changelog[0], self.example.changelog[0])},
            {"version": "v0"},
        ):
            with self.assertRaises(ValidationError):
                self.definition(**changes)

    def test_registration_revalidates_copied_objects(self):
        invalid = self.example.model_copy(update={"template": "{sport.__class__}"})
        with self.assertRaises(ValidationError):
            PromptRegistry().register(invalid)


if __name__ == "__main__":
    unittest.main()
