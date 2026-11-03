"""Offline integration checks: budgets, resumability and measurement integrity."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import config
from core.groq_client import GroqAPIError, GroqClient
from eval.eval_runner import (ROOT, build_jobs, load_cases, run_jobs, read_checkpoint,
                              pending_jobs, main)


def response(finish="STOP", language="English"):
    body = {"status": "suggestions", "language": language, "recommendations": [
        {"title": "Discuss the decision", "action": "Ask your coach which teammate was available.",
         "rationale": "A discussion helps compare the options you described."}], "follow_up_questions": []}
    finish = {"STOP": "stop", "MAX_TOKENS": "length", "SAFETY": "content_filter"}.get(finish, finish)
    return {"choices": [{"message": {"role": "assistant", "content": json.dumps(body)},
                         "finish_reason": finish}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 30}}


class Transport:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0
    def generate(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    def close(self):
        pass


class EvalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cb6-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.directory = self.root / "results"
        self.cases = load_cases(ROOT / "eval/cases.synthetic.json")
        patcher = patch.object(config, "MODEL_NAME", "offline-test-model")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.delays = []
    def jobs(self, **kwargs):
        return build_jobs(self.cases[:1], temperatures=(0.2,), top_ps=(0.8,), **kwargs)
    def factory(self, outcomes):
        self.transport = Transport(outcomes)
        def create(**kwargs):
            return GroqClient(self.transport, cache_dir=self.root / "cache",
                                sleep=self.delays.append, **kwargs)
        return create
    def test_grid_and_local_exclusions(self):
        jobs = build_jobs(self.cases)
        self.assertEqual(len(jobs), 144)
        self.assertEqual(sum(j.preflight.may_generate for j in jobs), 54)
        self.assertEqual(len({j.key for j in jobs}), 144)
        self.assertEqual({job.parameters.temperature for job in jobs}, set(config.EVAL_TEMPERATURES))
        self.assertEqual({job.parameters.top_p for job in jobs}, set(config.EVAL_TOP_P_VALUES))
        self.assertEqual(len(build_jobs(self.cases, subset=2)), 2)
    def test_completed_resume_never_constructs_client(self):
        jobs = self.jobs(max_tokens=(256,))
        run_jobs(jobs, self.directory, client_factory=self.factory([response()]))
        def forbidden(**kwargs):
            self.fail("Completed resume must not initialize a client")
        result = run_jobs(jobs, self.directory, client_factory=forbidden)
        self.assertEqual(result["calls_this_invocation"], 0)
        self.assertEqual(len((self.directory / "runs.jsonl").read_text().splitlines()), 1)
    def test_rate_limit_retains_success_then_explicit_resume(self):
        jobs = self.jobs(max_tokens=(256, 512, 1024))
        limited = GroqAPIError(429)
        run_jobs(jobs, self.directory, client_factory=self.factory([response(), limited, limited, limited]))
        self.assertEqual(read_checkpoint(self.directory, jobs[0])["status"], "ok")
        self.assertEqual(read_checkpoint(self.directory, jobs[1])["status"], "rate_limited")
        self.assertIsNone(read_checkpoint(self.directory, jobs[2]))
        self.assertEqual(len(pending_jobs(jobs, self.directory, True)), 2)
        run_jobs(jobs, self.directory, retry_failed=True, client_factory=self.factory([response(), response()]))
        self.assertEqual(self.transport.calls, 2)
        self.assertEqual(len(list((self.directory / "receipts").glob("*.json"))), 4)
    def test_shared_call_budget_caps_actual_attempts(self):
        jobs = self.jobs(max_tokens=(256,512))
        result = run_jobs(jobs, self.directory, max_calls=1, client_factory=self.factory([response()]))
        self.assertEqual(result["calls_this_invocation"], 1)
        self.assertIsNone(read_checkpoint(self.directory, jobs[1]))
    def test_client_disk_cache_without_checkpoint(self):
        jobs = self.jobs(max_tokens=(256,))
        run_jobs(jobs, self.directory, client_factory=self.factory([response()]))
        for path in (self.directory / "checkpoints").glob("*.json"):
            path.unlink()
        result = run_jobs(jobs, self.directory, client_factory=self.factory([]))
        self.assertEqual(result["calls_this_invocation"], 0)
        self.assertTrue(read_checkpoint(self.directory, jobs[0])["cache_hit"])
    def test_token_limit_and_repair_metrics_not_overwritten(self):
        jobs = self.jobs(max_tokens=(256,))
        run_jobs(jobs, self.directory, sleep_seconds=3, client_factory=self.factory([response("MAX_TOKENS"),response()]))
        row = read_checkpoint(self.directory, jobs[0])
        self.assertEqual(row["initial_finish_reason"], "MAX_TOKENS")
        self.assertFalse(row["initial_schema_valid"])
        self.assertTrue(row["complete_structured_response"])
        self.assertTrue(row["any_token_limit"])
        self.assertEqual(row["output_tokens"], 60)
        self.assertEqual(row["final_output_chars"], len(row["raw_output"]))
        self.assertEqual(self.delays, [3,3])
        with (self.directory / "tuning.csv").open(newline="",encoding="utf-8") as file:
            tuning = list(csv.DictReader(file))[0]
        self.assertEqual(tuning["max_tokens"], "256")
        self.assertEqual(tuning["complete_response_rate"], "1.0")
    def test_local_notices_have_no_model_completeness(self):
        jobs = build_jobs([self.cases[-1]], subset=1)
        run_jobs(jobs, self.directory, client_factory=lambda **kwargs:self.fail("local check called API"))
        row = read_checkpoint(self.directory,jobs[0])
        self.assertIsNone(row["schema_valid"])
        self.assertEqual(row["calls_made"],0)
    def test_tamil_uses_core_language_contract(self):
        jobs = build_jobs([self.cases[4]], subset=1)
        self.assertEqual(jobs[0].preflight.request.language,"Tamil")
        run_jobs(jobs,self.directory,client_factory=self.factory([response(language="Tamil")]))
        self.assertTrue(read_checkpoint(self.directory,jobs[0])["schema_valid"])
    def test_revision_keys_change_with_input_or_model(self):
        old = self.jobs(max_tokens=(256,))[0].key
        self.cases[0].values["goal"] = "Compare two passing options"
        self.assertNotEqual(old,self.jobs(max_tokens=(256,))[0].key)
        old = self.jobs(max_tokens=(256,))[0].key
        with patch.object(config,"MODEL_NAME","different-model"):
            self.assertNotEqual(old,self.jobs(max_tokens=(256,))[0].key)
    def test_corrupt_checkpoint_stops_instead_of_spending(self):
        jobs = self.jobs(max_tokens=(256,))
        run_jobs(jobs,self.directory,client_factory=self.factory([response()]))
        next((self.directory / "checkpoints").glob("*.json")).write_text("{",encoding="utf-8")
        with self.assertRaises(ValueError):
            run_jobs(jobs,self.directory,client_factory=self.factory([]))
        self.assertEqual(self.transport.calls,0)
    def test_invalid_cases_and_grid_rejected(self):
        with self.assertRaises(ValueError):
            load_cases(ROOT / "eval/cases.student.template.json")
        with self.assertRaises(ValueError):
            build_jobs(self.cases,subset=0)
        with self.assertRaises(ValueError):
            build_jobs(self.cases,max_tokens=(1,))
        with self.assertRaises(ValueError):
            build_jobs([],subset=1)
    def test_default_cli_is_dry_and_needs_no_key(self):
        with patch.object(GroqClient,"from_streamlit",side_effect=AssertionError("no API")):
            self.assertEqual(main(["--subset","2","--output",str(self.directory)]),0)
        self.assertFalse(self.directory.exists())


if __name__ == "__main__":
    unittest.main()
