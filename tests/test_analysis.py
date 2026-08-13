import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyze import first_failed_step, percentile


class AnalysisTests(unittest.TestCase):
    def test_percentile(self):
        self.assertEqual(percentile([10, 20, 30], .5), 20)

    def test_failure_signature_uses_first_failed_step(self):
        job = {"steps": [
            {"number": 1, "name": "Checkout", "conclusion": "success"},
            {"number": 2, "name": "Tests", "conclusion": "failure"},
            {"number": 3, "name": "Upload", "conclusion": "failure"},
        ]}
        self.assertEqual(first_failed_step(job), "Tests")


if __name__ == "__main__":
    unittest.main()
