#!/usr/bin/env python3
"""Acquire public GitHub Actions metadata through the authenticated gh CLI."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPOSITORY = "pandas-dev/pandas"


def gh(path):
    result = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def fetch_all_jobs(run_id, endpoints):
    jobs = []
    page = 1
    while True:
        endpoint = f"repos/{REPOSITORY}/actions/runs/{run_id}/jobs?per_page=100&page={page}"
        payload = gh(endpoint)
        endpoints.append(endpoint)
        jobs.extend(payload["jobs"])
        if len(jobs) >= payload["total_count"]:
            return jobs, payload["total_count"]
        page += 1


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    runs = []
    endpoints = []
    for page in range(1, 4):
        endpoint = f"repos/{REPOSITORY}/actions/runs?per_page=100&page={page}&status=completed"
        payload = gh(endpoint)
        endpoints.append(endpoint)
        runs.extend(payload["workflow_runs"])
    selected_runs = [{key: run.get(key) for key in (
        "id", "name", "event", "status", "conclusion", "created_at", "run_started_at",
        "updated_at", "head_branch", "head_sha", "run_attempt", "html_url")}
        for run in runs]
    jobs = []
    job_counts_by_run = {}
    for run in selected_runs:
        if run["conclusion"] != "failure":
            continue
        run_jobs, total_count = fetch_all_jobs(run["id"], endpoints)
        job_counts_by_run[str(run["id"])] = total_count
        for job in run_jobs:
            jobs.append({
                "run_id": run["id"], "job_id": job["id"], "name": job["name"],
                "status": job["status"], "conclusion": job["conclusion"],
                "started_at": job["started_at"], "completed_at": job["completed_at"],
                "html_url": job["html_url"],
                "steps": [{key: step.get(key) for key in ("name", "status", "conclusion", "number", "started_at", "completed_at")}
                          for step in job.get("steps", [])],
            })
    runs_path = RAW / "workflow_runs.json"
    jobs_path = RAW / "failed_run_jobs.json"
    runs_path.write_text(json.dumps(selected_runs, indent=2) + "\n")
    jobs_path.write_text(json.dumps(jobs, indent=2) + "\n")
    manifest = {
        "source": "GitHub REST API",
        "repository": REPOSITORY,
        "documentation": "https://docs.github.com/en/rest/actions/workflow-runs",
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "selection": "first 3 pages of completed workflow runs, 100 per page, at retrieval time",
        "workflow_runs": len(selected_runs),
        "failed_runs": sum(run["conclusion"] == "failure" for run in selected_runs),
        "failed_run_jobs": len(jobs),
        "job_counts_by_failed_run": job_counts_by_run,
        "endpoints": endpoints,
        "sha256": {
            runs_path.name: hashlib.sha256(runs_path.read_bytes()).hexdigest(),
            jobs_path.name: hashlib.sha256(jobs_path.read_bytes()).hexdigest(),
        },
        "privacy": "Only metadata already public in pandas-dev/pandas Actions was collected; logs were not downloaded.",
    }
    (RAW / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {len(selected_runs)} runs, {manifest['failed_runs']} failures, {len(jobs)} failure-run jobs")


if __name__ == "__main__":
    main()
