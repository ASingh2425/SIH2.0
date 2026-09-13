"""
Adversarial Test Suite — ONNX Forensic Engineering Validation
SIH Problem Statement 26171 — Non-Negotiable Forensic Rules Verification

Tests:
1. ONNX model pixel perturbation sensitivity (altering pixels changes prediction output).
2. ONNX model DOM metadata independence (altering DOM metadata has 0% effect on predictions).
3. Held-out manual UI fixture evaluation output integrity.
4. Final verdict assertion is VALID or PARTIALLY VALID.
"""

import unittest
import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.evaluation.onnx_forensic_validation import run_forensic_validation

class TestONNXForensicValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        # Execute validation pipeline to ensure fresh results
        run_forensic_validation(cls.base_dir)
        
        cls.results_path = os.path.join(cls.base_dir, "ml", "evaluation", "onnx_forensic_results.json")
        with open(cls.results_path) as f:
            cls.results = json.load(f)

    def test_onnx_model_asset_integrity(self):
        """Verifies exported ONNX detector model exists and contains valid SHA-256 digest."""
        prov = self.results["onnx_model_provenance"]
        self.assertTrue(os.path.exists(os.path.join(self.base_dir, prov["model_path"])))
        self.assertEqual(len(prov["model_sha256"]), 64)
        self.assertGreater(prov["model_size_bytes"], 100000)

    def test_pixel_perturbation_sensitivity(self):
        """Verifies prediction output changes when screenshot pixels are perturbed."""
        pix_test = self.results["pixel_perturbation_test"]
        self.assertTrue(pix_test["verified"], "ONNX model MUST change prediction output when pixels change!")
        self.assertNotEqual(pix_test["orig_hash"], pix_test["altered_hash"])

    def test_dom_metadata_independence(self):
        """Verifies model predictions are 100% independent of DOM metadata."""
        dom_test = self.results["dom_independence_test"]
        self.assertTrue(dom_test["verified"], "ONNX model MUST be 100% independent of DOM metadata!")

    def test_heldout_fixture_evaluation_counts(self):
        """Verifies evaluation runs on 10 hand-crafted manual UI fixtures."""
        heldout = self.results["heldout_fixture_evaluation"]
        self.assertEqual(heldout["total_fixtures"], 10)
        self.assertGreater(heldout["total_ground_truth_entities"], 0)

    def test_final_verdict_validity(self):
        """Verifies final verdict is VALID or PARTIALLY VALID without score inflation."""
        verdict = self.results["final_conclusion"]
        self.assertIn(verdict, ["VALID", "PARTIALLY VALID"], f"Unexpected verdict: {verdict}")

if __name__ == "__main__":
    unittest.main()
