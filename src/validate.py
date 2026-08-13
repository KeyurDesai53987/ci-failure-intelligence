import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def main():
    manifest = json.loads((RAW / "source_manifest.json").read_text())
    failures = []
    for filename, expected in manifest["sha256"].items():
        actual = hashlib.sha256((RAW / filename).read_bytes()).hexdigest()
        if actual != expected:
            failures.append(filename)
    runs = json.loads((RAW / "workflow_runs.json").read_text())
    jobs = json.loads((RAW / "failed_run_jobs.json").read_text())
    if len(runs) != manifest["workflow_runs"]:
        failures.append("workflow run count")
    if len({run["id"] for run in runs}) != len(runs):
        failures.append("duplicate run IDs")
    if len(jobs) != manifest["failed_run_jobs"]:
        failures.append("failed-run job count")
    if len({job["job_id"] for job in jobs}) != len(jobs):
        failures.append("duplicate job IDs")
    run_ids = {run["id"] for run in runs}
    failed_run_ids = {run["id"] for run in runs if run["conclusion"] == "failure"}
    job_run_ids = {job["run_id"] for job in jobs}
    if not job_run_ids.issubset(run_ids):
        failures.append("jobs reference uncaptured runs")
    if job_run_ids != failed_run_ids:
        failures.append("failed-run job coverage")
    actual_counts = {str(run_id): sum(job["run_id"] == run_id for job in jobs) for run_id in failed_run_ids}
    if actual_counts != manifest["job_counts_by_failed_run"]:
        failures.append("per-run job counts")
    failed_jobs_without_step = [job["job_id"] for job in jobs if job["conclusion"] == "failure"
                                and not any(step["conclusion"] == "failure" for step in job.get("steps", []))]
    if failed_jobs_without_step:
        failures.append("failed jobs without failed step")
    if failures:
        raise SystemExit("validation failed: " + ", ".join(failures))
    print(f"validated hashes, {len(runs)} unique runs, {len(jobs)} unique jobs, coverage, and failed steps")


if __name__ == "__main__":
    main()
