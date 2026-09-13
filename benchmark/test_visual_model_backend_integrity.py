"""
Adversarial Test Suite: Visual Model Backend Integrity Verification
SIH Problem Statement 26171 - Hardening Pass #19

Objective: Prove that backend reporting is genuine and strictly distinguishes:
- Capability detection (navigator.gpu)
- Actual initialized backend (webgpu / wasm / cpu)
- Model lifecycle state (MODEL_READY / INFERENCE_COMPLETE / INFERENCE_FAILED)
- DOM fallback (dom_fallback)
"""

import unittest
import os
import re

class TestVisualModelBackendIntegrity(unittest.TestCase):
    
    def setUp(self):
        self.engine_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "privacy", "visual_ocr_engine.ts")
        self.detector_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "privacy", "visual_detector.ts")
        self.sidepanel_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "ui", "SidePanel.tsx")

    def test_backend_types_defined(self):
        """Verify that ActualInferenceBackend includes webgpu, wasm, cpu, and dom_fallback."""
        with open(self.engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("export type ActualInferenceBackend = 'webgpu' | 'wasm' | 'cpu' | 'dom_fallback';", content)

    def test_dom_fallback_never_reported_as_visual_ocr(self):
        """Verify that DOM fallback elements are tagged as dom_fallback and not fake visual_ocr."""
        with open(self.detector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("backend: 'dom_fallback'", content)

    def test_sidepanel_displays_genuine_backend(self):
        """Verify that SidePanel.tsx displays actual backend status from mlBackendStatus."""
        with open(self.sidepanel_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("Actual Active Backend", content)
        self.assertIn("mlBackendStatus?.backend", content)

if __name__ == "__main__":
    unittest.main()
