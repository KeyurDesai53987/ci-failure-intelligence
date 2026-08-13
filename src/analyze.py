#!/usr/bin/env python3
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"


def parse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def percentile(values, q):
    if not values:
        return None
    values = sorted(values); pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] if lo == hi else values[lo] + (values[hi] - values[lo]) * (pos - lo)


def first_failed_step(job):
    for step in sorted(job.get("steps", []), key=lambda x: x.get("number") or 0):
        if step.get("conclusion") == "failure":
            return step["name"]
    return "No failed step exposed"


def main():
    runs = json.loads((RAW / "workflow_runs.json").read_text())
    jobs = json.loads((RAW / "failed_run_jobs.json").read_text())
    durations = []
    decisive_durations = []
    conclusions = Counter(run["conclusion"] or "null" for run in runs)
    by_workflow = defaultdict(Counter)
    for run in runs:
        by_workflow[run["name"]][run["conclusion"] or "null"] += 1
        start, end = parse(run["run_started_at"]), parse(run["updated_at"])
        if start and end and end >= start:
            duration = (end - start).total_seconds() / 60
            durations.append(duration)
            if run["conclusion"] in {"success", "failure"}:
                decisive_durations.append(duration)
    failed_jobs = [job for job in jobs if job["conclusion"] == "failure"]
    step_signatures = Counter(first_failed_step(job) for job in failed_jobs)
    workflow_rows = []
    for name, counts in by_workflow.items():
        decisive = counts["success"] + counts["failure"]
        workflow_rows.append({
            "workflow": name,
            "observed_runs": sum(counts.values()),
            "success": counts["success"], "failure": counts["failure"],
            "cancelled": counts["cancelled"], "skipped": counts["skipped"],
            "failure_rate_decisive_runs": counts["failure"] / decisive if decisive else "",
        })
    workflow_rows.sort(key=lambda row: (row["failure"], row["observed_runs"]), reverse=True)
    PROCESSED.mkdir(parents=True, exist_ok=True); RESULTS.mkdir(exist_ok=True)
    with (PROCESSED / "workflow_reliability.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=workflow_rows[0].keys()); writer.writeheader(); writer.writerows(workflow_rows)
    summary = {
        "observed_runs": len(runs), "conclusions": dict(conclusions),
        "decisive_failure_rate": conclusions["failure"] / (conclusions["failure"] + conclusions["success"]),
        "all_run_duration_minutes": {"median": percentile(durations, .5), "p90": percentile(durations, .9)},
        "decisive_run_duration_minutes": {"median": percentile(decisive_durations, .5), "p90": percentile(decisive_durations, .9)},
        "failed_run_jobs_observed": len(jobs), "failed_jobs": len(failed_jobs),
        "first_failed_step_signatures": step_signatures.most_common(),
        "workflows_with_most_failures": workflow_rows[:10],
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
