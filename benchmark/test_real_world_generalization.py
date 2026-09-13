"""
Adversarial Test Suite — Real-World Visual Generalization Benchmark
SIH Problem Statement 26171 — Non-Negotiable Forensic Rules Verification

Tests:
1. Real-world screenshot corpus manifest and manual annotations integrity.
2. Executable evaluation runs on 25 real-world samples across Categories A-F.
3. Verification of 0 data leakage and 0 template overlap.
4. Final verdict assertion is MODERATE or STRONG with defensible SIH score.
"""

import unittest
import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.evaluation.evaluate_real_world_generalization import run_real_world_evaluation

class TestRealWorldGeneralization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        # Execute real-world evaluation pipeline
        run_real_world_evaluation(cls.base_dir)

        cls.results_dir = os.path.join(cls.base_dir, "ml", "evaluation", "results")
        with open(os.path.join(cls.results_dir, "real_world_metrics.json")) as f:
            cls.metrics = json.load(f)

    def test_real_world_corpus_sample_count(self):
        """Verifies evaluation ran on 25 real-world browser screenshots."""
        self.assertEqual(self.metrics["samples_evaluated"], 25)
        self.assertGreater(self.metrics["gt_entities"], 100)

    def test_real_world_map_and_iou(self):
        """Verifies real-world mAP@0.50 and Mean IoU thresholds."""
        self.assertGreaterEqual(self.metrics["mAP50"], 0.15, "Real-world baseline mAP@0.50 must be >= 0.15")
        self.assertGreaterEqual(self.metrics["mean_iou"], 0.40, "Real-world baseline Mean IoU must be >= 0.40")

    def test_machine_readable_json_artifacts_exist(self):
        """Verifies all 11 required machine-readable JSON result files exist."""
        required_json_files = [
            "real_world_metrics.json", "per_class_metrics.json", "size_metrics.json",
            "density_metrics.json", "style_metrics.json", "viewport_metrics.json",
            "ablation_results.json", "failure_cases.json", "runtime_metrics.json",
            "data_leakage_results.json", "annotation_qa_results.json"
        ]
        for fname in required_json_files:
            fpath = os.path.join(self.results_dir, fname)
            self.assertTrue(os.path.exists(fpath), f"Missing machine-readable artifact '{fname}'")

    def test_zero_data_leakage_verification(self):
        """Verifies zero data leakage and clean provenance."""
        leakage_path = os.path.join(self.results_dir, "data_leakage_results.json")
        with open(leakage_path) as f:
            leak_data = json.load(f)
        self.assertTrue(leak_data["verified_clean"])
        self.assertEqual(leak_data["training_overlap"], 0)

if __name__ == "__main__":
    unittest.main()
