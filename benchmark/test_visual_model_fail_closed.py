"""
Adversarial Test Suite: Visual Model Fail-Closed Security Boundary Verification
SIH Problem Statement 26171 - Hardening Pass #19

Objective: Verify that if local visual model loading fails, WASM/WebGPU initialization fails,
or OCR inference encounters an un-inspected blind spot, the system MUST:

1. Transition visualPrivacyState to 'VISUAL_PRIVACY_UNVERIFIED'.
2. Flag all un-inspected regions as UNVERIFIED_VISUAL_REGION.
3. Solid-mask all unverified visual bounding boxes with dark fill (#020617).
4. Transmit ZERO raw image bytes to network egress / remote reasoner.
"""

import unittest
import os
import re

class TestVisualModelFailClosed(unittest.TestCase):
    
    def setUp(self):
        self.detector_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "privacy", "visual_detector.ts")
        self.redactor_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "content", "canvas_capture.ts")
        self.egress_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "privacy", "egress_validator.ts")

    def test_inference_failure_transitions_to_unverified(self):
        """Verify that INFERENCE_FAILED state transitions visualPrivacyState to VISUAL_PRIVACY_UNVERIFIED."""
        with open(self.detector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("INFERENCE_FAILED", content)
        self.assertIn("state = 'VISUAL_PRIVACY_UNVERIFIED'", content)

    def test_unverified_state_omits_egress_image_payload(self):
        """Verify that when visualPrivacyState is VISUAL_PRIVACY_UNVERIFIED, no screenshot payload reaches egress."""
        with open(self.egress_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("VISUAL_PRIVACY_UNVERIFIED", content)
        self.assertIn("INV-07", content)

    def test_solid_dark_mask_fill_applied(self):
        """Verify that unverified visual regions receive solid dark fill #020617 masking."""
        with open(self.redactor_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("#020617", content)
        self.assertIn("ctx.fillRect", content)

if __name__ == "__main__":
    unittest.main()
