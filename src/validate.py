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
    if len(runs) != manifest["workflow_runs"]:
        failures.append("workflow run count")
    if len({run["id"] for run in runs}) != len(runs):
        failures.append("duplicate run IDs")
    if failures:
        raise SystemExit("validation failed: " + ", ".join(failures))
    print(f"validated hashes and {len(runs)} unique factual workflow runs")


if __name__ == "__main__":
    main()
