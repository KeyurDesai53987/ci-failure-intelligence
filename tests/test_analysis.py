import unittest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyze import first_failed_step, percentile


class AnalysisTests(unittest.TestCase):
    def test_percentile(self):
        self.assertEqual(percentile([10, 20, 30], .5), 20)

    def test_failure_signature_uses_first_failed_step(self):
        path = Path(__file__).resolve().parents[1] / "data" / "raw" / "failed_run_jobs.json"
        jobs = json.loads(path.read_text())
        job = next(item for item in jobs if item["job_id"] == 90357844380)
        self.assertEqual(first_failed_step(job), "Clean closed pull request caches")


if __name__ == "__main__":
    unittest.main()
