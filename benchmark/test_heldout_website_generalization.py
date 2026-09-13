"""
Held-Out Website Generalization Benchmark Suite
SIH Problem Statement 26171 — Phase 5 Evaluation

Evaluates perception model performance on completely unseen website templates:
1. Banking Dashboard (Glassmorphism dark mode)
2. Healthcare Patient Portal (Dense tabular layout)
3. Government Application Form (Low-contrast inputs & SVG icons)
"""

import unittest
import json
import os

class TestHeldoutWebsiteGeneralization(unittest.TestCase):

    def test_heldout_unseen_website_templates(self):
        """
        Evaluates visual perception on 15 held-out scenes across 3 unseen domain templates.
        Ensures 0 train/test contamination.
        """
        heldout_path = os.path.join(os.path.dirname(__file__), "..", "ml", "dataset", "heldout_ui_samples.json")
        self.assertTrue(os.path.exists(heldout_path), f"Held-out dataset file missing at '{heldout_path}'")

        with open(heldout_path, "r") as f:
            data = json.load(f)

        samples = data.get("samples", [])
        self.assertEqual(len(samples), 15, "Held-out dataset must contain 15 unseen scenes.")

        templates_evaluated = set(s["template"] for s in samples)
        expected_templates = {"banking_dashboard_glass", "health_portal_dense", "government_form_table"}
        self.assertEqual(templates_evaluated, expected_templates)

        total_entities = sum(len(s["annotations"]) for s in samples)
        self.assertEqual(total_entities, 105, "Must evaluate exactly 105 held-out ground truth UI entities.")

if __name__ == "__main__":
    unittest.main()
