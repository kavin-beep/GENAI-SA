"""Offline Streamlit interaction checks; all generation is mocked."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import config
from core.feedback import FeedbackEvent, save_feedback
from core.groq_client import SetupError
from core.schemas import CoachingResponse, GenerationResult, Recommendation, GenerationRequest


class UITests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(config.PROJECT_ROOT / "app.py"), default_timeout=30).run()
        self.assertFalse(self.app.exception)

    def fill(self):
        for key, text in {"input_sport": "football", "input_position": "midfielder", "input_region": "test region",
                          "input_available_resources": "school coach"}.items():
            self.app.text_input(key=key).set_value(text)
        self.app.number_input(key="input_age").set_value(15)
        self.app.text_area(key="input_situation").set_value("I missed a communication opportunity.")
        self.app.text_area(key="input_goal").set_value("Understand communication choices")
        self.app.radio(key="injury_status").set_value("None reported")
        for key in ("pain", "concussion", "urgent"):
            self.app.radio(key=key).set_value("No")
        self.app.run()

    def click_submit(self):
        next(button for button in self.app.button if button.label == "Get suggestions").click().run()
        self.assertFalse(self.app.exception)

    def good_result(self, language="English"):
        return GenerationResult(status="ok", message="ok", data=CoachingResponse(
            status="suggestions", language=language, recommendations=[Recommendation(
                title="Discuss the decision", action="Discuss the decision with your coach.",
                rationale="A conversation can clarify the options.")], follow_up_questions=[]))

    def test_default_english_and_unanswered_health(self):
        self.assertEqual(self.app.selectbox(key="language_choice").value, "English")
        for key in ("injury_status", "pain", "concussion", "urgent"):
            self.assertIsNone(self.app.radio(key=key).value)

    def test_fictional_sample_prefills_form_without_calling_model(self):
        sample_button = next(button for button in self.app.button if button.label == "Try a fictional sample")
        with patch("ui.controller.GroqClient.from_streamlit") as client:
            sample_button.click().run()
            client.assert_not_called()
        self.assertEqual(self.app.text_input(key="input_sport").value, "Football")
        self.assertEqual(self.app.text_input(key="input_position").value, "Midfielder")
        self.assertEqual(self.app.number_input(key="input_age").value, 15)
        self.assertEqual(self.app.text_area(key="input_situation").value,
                         "I passed to a marked teammate while another teammate was free.")
        self.assertEqual(self.app.radio(key="injury_status").value, "None reported")
        self.assertTrue(any("Fictional sample loaded" in item.value for item in self.app.success))

    def test_empty_submit_no_client(self):
        with patch("ui.controller.GroqClient.from_streamlit") as client:
            self.click_submit()
            client.assert_not_called()
        self.assertEqual(self.app.session_state.current_submission.view.state, "incomplete")

    def test_urgent_answer_before_other_fields_no_client(self):
        self.app.radio(key="urgent").set_value("Yes").run()
        with patch("ui.controller.GroqClient.from_streamlit") as client:
            self.click_submit()
            client.assert_not_called()
        self.assertEqual(self.app.session_state.current_submission.view.state, "local_notice")
        self.assertTrue(any("urgent medical help" in text.value for text in self.app.text))

    def test_missing_api_setup_friendly(self):
        self.fill()
        with patch("ui.controller.GroqClient.from_streamlit", side_effect=SetupError("Add private Streamlit secrets.")):
            self.click_submit()
        self.assertTrue(any("Add private Streamlit secrets" in item.value for item in self.app.info))

    def test_success_rationale_download_and_rerun_no_regeneration(self):
        self.fill()
        with patch("ui.controller.GroqClient.from_streamlit") as factory:
            client = factory.return_value.__enter__.return_value
            client.generate.return_value = self.good_result()
            self.click_submit()
            self.app.run()
            self.assertEqual(client.generate.call_count, 1)
        self.assertTrue(any(item.value == "**Rationale**" for item in self.app.markdown))
        self.assertTrue(any("conversation can clarify" in item.value for item in self.app.text))
        self.assertTrue(any(button.label == "Download my plan (.md)" for button in self.app.get("download_button")))

    def test_edit_hides_stale_result_and_retains_other_inputs(self):
        self.fill()
        with patch("ui.controller.GroqClient.from_streamlit") as factory:
            factory.return_value.__enter__.return_value.generate.return_value = self.good_result()
            self.click_submit()
        self.app.text_input(key="input_sport").set_value("cricket").run()
        self.assertEqual(self.app.text_input(key="input_position").value, "midfielder")
        self.assertFalse(self.app.get("download_button"))
        self.assertTrue(any("details changed" in item.value for item in self.app.info))

    def test_selected_language_sent_explicitly(self):
        self.fill()
        self.app.selectbox(key="language_choice").set_value("Tamil").run()
        with patch("ui.controller.GroqClient.from_streamlit") as factory:
            client = factory.return_value.__enter__.return_value
            client.generate.return_value = self.good_result(language="Tamil")
            self.click_submit()
            self.assertEqual(client.generate.call_args.args[0].language, "Tamil")

    def test_other_language_name_and_combining_marks(self):
        self.fill()
        self.app.selectbox(key="language_choice").set_value("Other language").run()
        self.app.text_input(key="other_language").set_value("தமிழ்").run()
        with patch("ui.controller.GroqClient.from_streamlit") as factory:
            client = factory.return_value.__enter__.return_value
            client.generate.return_value = self.good_result(language="தமிழ்")
            self.click_submit()
            self.assertEqual(client.generate.call_args.args[0].language, "தமிழ்")

    def test_unknown_health_never_calls_model(self):
        self.fill()
        self.app.radio(key="pain").set_value("Not sure").run()
        with patch("ui.controller.GroqClient.from_streamlit") as factory:
            self.click_submit()
            factory.assert_not_called()

    def test_unsafe_cached_advice_not_rendered(self):
        self.fill()
        result = self.good_result()
        result.data.recommendations[0].action = "Train through pain."
        result.cache_hit = True
        with patch("ui.controller.GroqClient.from_streamlit") as factory:
            factory.return_value.__enter__.return_value.generate.return_value = result
            self.click_submit()
        self.assertEqual(self.app.session_state.current_submission.view.state, "withheld")
        self.assertFalse(any("Train through pain" in item.value for item in self.app.text))

    def test_feedback_deduplicates_without_generation(self):
        self.fill()
        with patch("ui.controller.GroqClient.from_streamlit") as factory, patch("ui.components.save_feedback", return_value=True) as save:
            client = factory.return_value.__enter__.return_value
            client.generate.return_value = self.good_result()
            self.click_submit()
            self.app.get("feedback")[0].set_value(1).run()
            self.app.run()
            self.assertEqual(save.call_count, 1)
            self.assertEqual(client.generate.call_count, 1)
            self.assertEqual(json.loads(self.app.session_state.feedback_events[0])["vote"], "up")

    def test_feedback_failure_preserves_download(self):
        self.fill()
        with patch("ui.controller.GroqClient.from_streamlit") as factory, patch("ui.components.save_feedback", return_value=False):
            factory.return_value.__enter__.return_value.generate.return_value = self.good_result()
            self.click_submit()
            self.app.get("feedback")[0].set_value(0).run()
        self.assertTrue(any("Local storage" in item.value for item in self.app.warning))
        self.assertTrue(any(item.label == "Download my feedback (.jsonl)" for item in self.app.get("download_button")))

    def test_separate_browser_sessions_have_separate_feedback_ids(self):
        second = AppTest.from_file(str(config.PROJECT_ROOT / "app.py"), default_timeout=30).run()
        self.assertNotEqual(self.app.session_state.feedback_session_id, second.session_state.feedback_session_id)

    def test_feedback_file_contains_no_sport_or_health_inputs(self):
        parent = config.PROJECT_ROOT / ".cache" / "tests"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            event = FeedbackEvent(result_id="a" * 32, prompt_id="tactical_reflection", prompt_version="v1", vote="up")
            self.assertTrue(save_feedback(event, "b" * 32, directory=Path(directory)))
            data = json.loads((Path(directory) / ("b" * 32) / "feedback.jsonl").read_text())
            self.assertEqual(set(data), {"event_id", "result_id", "prompt_id", "prompt_version", "vote", "recorded_at"})


if __name__ == "__main__":
    unittest.main()
