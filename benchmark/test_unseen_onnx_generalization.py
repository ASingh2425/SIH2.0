"""
Unseen ONNX Perception Generalization & ML Pipeline Test Suite
SIH Problem Statement 26171 — Unseen Dataset Verification
"""

import unittest
import os

from ml.evaluation.gated_evaluation_runner import run_gated_evaluation_pipeline

class TestUnseenONNXGeneralization(unittest.TestCase):

    def test_gated_evaluation_pipeline_execution(self):
        """Runs full gated evaluation pipeline on unseen challenge dataset and verifies zero data leakage."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        success = run_gated_evaluation_pipeline(base_dir)
        self.assertTrue(success, "Gated evaluation pipeline must pass all quantitative gating criteria.")

if __name__ == "__main__":
    unittest.main()
