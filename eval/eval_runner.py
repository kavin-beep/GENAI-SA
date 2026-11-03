"""Plan by default; execute an explicitly budgeted, resumable parameter sweep.

Run from the repository root: python -m eval.eval_runner --help.
Private checkpoints are authoritative; JSONL/CSV are rebuilt views of selected jobs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import math
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

import config
from core.formatter import format_result
from core.groq_client import CallBudget, GroqClient, SetupError
from core.prompts import REGISTRY
from core.safety import HealthContext, Preflight, prepare_request
from core.schemas import GenerationParameters, GenerationResult, StrictModel
from pydantic import Field

ROOT = Path(__file__).resolve().parents[1]
RETRYABLE = {"rate_limited", "network_error", "service_error", "budget_exhausted",
             "configuration_error", "authentication_error", "model_unavailable"}


class EvalCase(StrictModel):
    """One supplied input case; health answers are explicit, never inferred."""
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$", max_length=80)
    prompt_id: str
    values: dict[str, str]
    health: HealthContext
    language: str = "English"
    provenance: str = "student_supplied"


@dataclass(frozen=True)
class Job:
    key: str
    case: EvalCase
    version: str
    parameters: GenerationParameters
    preflight: Preflight


def load_cases(path: Path) -> list[EvalCase]:
    """Reject duplicate IDs and authoring placeholders before any provider call."""
    raw = path.read_text(encoding="utf-8")
    if "[MY INPUT NEEDED" in raw:
        raise ValueError("Replace case placeholders before running evaluation.")
    cases = [EvalCase.model_validate_json(json.dumps(item)) for item in json.loads(raw)]
    if not cases or len({case.id for case in cases}) != len(cases):
        raise ValueError("Supply at least one case with unique case IDs.")
    return cases


def build_jobs(cases: list[EvalCase], *, temperatures=config.EVAL_TEMPERATURES,
               top_ps=config.EVAL_TOP_P_VALUES, max_tokens=config.EVAL_MAX_TOKENS_VALUES,
               all_versions: bool = False, subset: int | None = None) -> list[Job]:
    """Stable ordering across every configured parameter axis."""
    if subset is not None and subset < 1:
        raise ValueError("subset must be positive")
    if not temperatures or not top_ps or not max_tokens:
        raise ValueError("Each grid axis needs at least one value")
    entries = REGISTRY.entries(all_versions=all_versions)
    registered = {entry.id for entry in entries}
    supplied = {case.prompt_id for case in cases}
    if registered != supplied:
        raise ValueError(f"Case coverage mismatch. Missing: {registered-supplied}; unknown: {supplied-registered}")
    # Include implementation and model identity so stale results cannot mask edits.
    digest = hashlib.sha256()
    for path in [ROOT / "config.py", Path(__file__), *sorted((ROOT / "core").glob("*.py"))]:
        digest.update(path.read_bytes())
    revision = digest.hexdigest()
    grid = [GenerationParameters(temperature=float(t), top_p=float(p), max_tokens=n)
            for t, p, n in itertools.product(temperatures, top_ps, max_tokens)]
    jobs = []
    for entry in entries:
        for case in cases:
            if case.prompt_id != entry.id:
                continue
            for params in grid:
                preflight = prepare_request(entry, case.values, case.health,
                                            language=case.language, parameters=params)
                identity = {"revision": revision, "model": config.MODEL_NAME,
                            "case": case.model_dump(), "version": entry.version,
                            "params": params.model_dump(), "preflight": preflight.model_dump()}
                key = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                jobs.append(Job(key, case, entry.version, params, preflight))
    return jobs[:subset] if subset else jobs


def checkpoint_path(directory: Path, job: Job) -> Path:
    return directory / "checkpoints" / f"{job.key}.json"


def read_checkpoint(directory: Path, job: Job) -> dict | None:
    """A corrupt checkpoint stops the run rather than silently spending quota again."""
    path = checkpoint_path(directory, job)
    if not path.exists():
        return None
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("job_id") != job.key:
        raise ValueError("Checkpoint identity mismatch; preserve and inspect the file.")
    return row


def pending_jobs(jobs: list[Job], directory: Path, retry_failed: bool = False) -> list[Job]:
    return [job for job in jobs if (row := read_checkpoint(directory, job)) is None
            or (retry_failed and row["status"] in RETRYABLE)]


def atomic_text(path: Path, content: str) -> None:
    """Replace complete files atomically, including after interrupted prior runs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(uuid4().hex + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def make_row(job: Job, result: GenerationResult | None, wall_ms: int) -> dict:
    """Mechanical completeness metrics are not subjective quality scores."""
    attempts = result.attempts if result else []
    first = attempts[0] if attempts else None
    last = attempts[-1] if attempts else None
    view = format_result(job.preflight, result)
    def token_sum(name):
        values = [getattr(a, name) for a in attempts]
        return sum(values) if values and all(v is not None for v in values) else None
    return {
        "job_id": job.key, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "case_id": job.case.id, "provenance": job.case.provenance,
        "prompt_id": job.case.prompt_id, "version": job.version, "model": config.MODEL_NAME,
        "language": job.case.language, **job.parameters.model_dump(),
        "status": result.status if result else "local_notice", "display_state": view.state,
        "reason_codes": list(job.preflight.reason_codes), "latency_ms": wall_ms,
        "provider_latency_ms": sum(a.latency_ms for a in attempts),
        "calls_made": result.calls_made if result else 0,
        "cache_hit": result.cache_hit if result else False,
        "input_tokens": token_sum("input_tokens"), "output_tokens": token_sum("output_tokens"),
        "thinking_tokens": token_sum("thinking_tokens"),
        "initial_output_tokens": first.output_tokens if first else None,
        "final_output_tokens": last.output_tokens if last else None,
        "initial_output_chars": len(first.raw_output) if first else 0,
        "final_output_chars": len(last.raw_output) if last else 0,
        "final_whitespace_words": len(last.raw_output.split()) if last else 0,
        "initial_schema_valid": first.schema_valid if first else None,
        "schema_valid": last.schema_valid if last else None,
        "initial_finish_reason": first.finish_reason if first else "",
        "final_finish_reason": last.finish_reason if last else "",
        "complete_structured_response": bool(result and result.status == "ok" and result.data),
        "any_token_limit": any(a.finish_reason == "MAX_TOKENS" for a in attempts),
        "recommendation_count": len(result.data.recommendations) if result and result.data else 0,
        "raw_output": last.raw_output if last else "",
        "attempts": [a.model_dump() for a in attempts],
        "warnings": result.warnings if result else [],
    }


def export_results(jobs: list[Job], directory: Path) -> None:
    """Rebuild selected results and grouped tuning metrics from durable checkpoints."""
    import io
    rows = [row for job in jobs if (row := read_checkpoint(directory, job)) is not None]
    atomic_text(directory / "runs.jsonl", "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    flat = [{k: v for k, v in row.items() if k not in {"attempts", "raw_output", "warnings", "reason_codes"}}
            for row in rows]
    def write_csv(name, records):
        stream = io.StringIO(newline="")
        if records:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        atomic_text(directory / name, stream.getvalue())
    write_csv("summary.csv", flat)
    grouped = {}
    for row in rows:
        key = tuple(row[k] for k in ("prompt_id", "version", "language", "temperature", "top_p", "max_tokens"))
        grouped.setdefault(key, []).append(row)
    tuning = []
    for key, group in grouped.items():
        model_rows = [r for r in group if r["status"] != "local_notice"]
        def mean(field):
            vals = [r[field] for r in model_rows if r[field] is not None]
            return sum(vals) / len(vals) if vals else None
        tuning.append(dict(zip(("prompt_id", "version", "language", "temperature", "top_p", "max_tokens"), key)) | {
            "recorded_jobs": len(group), "model_jobs": len(model_rows),
            "local_notices": len(group) - len(model_rows),
            "mean_final_chars": mean("final_output_chars"),
            "mean_final_output_tokens": mean("final_output_tokens"),
            "mean_total_output_tokens": mean("output_tokens"),
            "initial_schema_valid_rate": mean("initial_schema_valid"),
            "complete_response_rate": mean("complete_structured_response"),
            "token_limit_rate": mean("any_token_limit"),
        })
    write_csv("tuning.csv", tuning)


def run_jobs(jobs: list[Job], directory: Path, *, max_calls: int = config.EVAL_DEFAULT_CALL_BUDGET,
             sleep_seconds: float = config.EVAL_SLEEP_SECONDS, retry_failed: bool = False,
             client_factory: Callable = GroqClient.from_streamlit) -> dict:
    """Checkpoint each job; stop at quota/access failures without discarding earlier work."""
    if max_calls < 0 or not math.isfinite(sleep_seconds) or sleep_seconds < 0:
        raise ValueError("Call budget and sleep must be nonnegative")
    directory.mkdir(parents=True, exist_ok=True)
    budget = CallBudget(max_calls)
    client = None
    completed = 0
    try:
        for job in pending_jobs(jobs, directory, retry_failed):
            result = None
            started = time.monotonic()
            if job.preflight.may_generate:
                if budget.used >= budget.limit:
                    break
                if client is None:
                    client = client_factory(cache_namespace="eval:" + str(directory.resolve()), sleep_seconds=sleep_seconds)
                result = client.generate(job.preflight.request, budget=budget)
            row = make_row(job, result, int((time.monotonic() - started) * 1000))
            # Every retry is retained as a separate receipt as well as the latest checkpoint.
            atomic_text(directory / "receipts" / f"{uuid4().hex}.json", json.dumps(row, ensure_ascii=False))
            atomic_text(checkpoint_path(directory, job), json.dumps(row, ensure_ascii=False))
            completed += 1
            if result and result.status in RETRYABLE:
                break
    finally:
        if client is not None:
            client.close()
        export_results(jobs, directory)
    return {"newly_recorded_jobs": completed, "calls_this_invocation": budget.used}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "eval/cases.synthetic.json")
    parser.add_argument("--output", type=Path, default=ROOT / "eval/results")
    parser.add_argument("--subset", type=int, help="First N grid jobs, not N cases")
    parser.add_argument("--temperatures", nargs="+", type=float, default=config.EVAL_TEMPERATURES)
    parser.add_argument("--top-p", nargs="+", type=float, default=config.EVAL_TOP_P_VALUES)
    parser.add_argument("--max-tokens", nargs="+", type=int, default=config.EVAL_MAX_TOKENS_VALUES)
    parser.add_argument("--max-calls", type=int, default=config.EVAL_DEFAULT_CALL_BUDGET)
    parser.add_argument("--sleep", type=float, default=config.EVAL_SLEEP_SECONDS, help="Seconds before every actual Groq request attempt")
    parser.add_argument("--all-versions", action="store_true")
    parser.add_argument("--retry-failed", action="store_true", help="Explicitly retry saved transient failures")
    parser.add_argument("--execute", action="store_true", help="Without this flag: plan only, zero requests")
    args = parser.parse_args(argv)
    try:
        if args.max_calls < 0 or not math.isfinite(args.sleep) or args.sleep < 0:
            raise ValueError("Call budget and sleep must be nonnegative")
        jobs = build_jobs(load_cases(args.cases), temperatures=args.temperatures, top_ps=args.top_p,
                          max_tokens=args.max_tokens, all_versions=args.all_versions, subset=args.subset)
        pending = pending_jobs(jobs, args.output, args.retry_failed)
        eligible = sum(job.preflight.may_generate for job in pending)
        ceiling = eligible * config.MAX_REQUEST_ATTEMPTS * (1 + config.MAX_SCHEMA_REPAIR_ATTEMPTS)
        print(json.dumps({"selected_jobs": len(jobs), "pending_jobs": len(pending),
                          "sampling_parameters_supported": config.MODEL_SUPPORTS_SAMPLING_PARAMETERS,
                          "temperature_points": len({job.parameters.temperature for job in jobs}),
                          "top_p_points": len({job.parameters.top_p for job in jobs}),
                          "max_tokens_points": len({job.parameters.max_tokens for job in jobs}),
                          "pending_local_checks": len(pending)-eligible,
                          "uncached_typical_calls": eligible, "uncached_retry_ceiling": ceiling,
                          "invocation_call_cap": min(args.max_calls, ceiling),
                          "mode": "execute" if args.execute else "plan_only"}, indent=2))
        if args.execute:
            print(json.dumps(run_jobs(jobs, args.output, max_calls=args.max_calls,
                                     sleep_seconds=args.sleep, retry_failed=args.retry_failed)))
        return 0
    except (ValueError, OSError, KeyError, SetupError) as exc:
        print(f"Evaluation stopped: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
