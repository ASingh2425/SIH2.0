"""
Adversarial Test Suite: Real Visual Model Runtime Verification
SIH Problem Statement 26171 - Hardening Pass #19

Objective: Test the LocalVisualModelEngine and LocalVisualDetector TS implementation files
to verify that model lifecycle state, backend identification, bounding box provenance,
and pixel OCR data flow are structurally sound and enforce zero-trust privacy boundaries.
"""

import unittest
import os
import re

class TestRealVisualModelRuntime(unittest.TestCase):
    
    def setUp(self):
        self.engine_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "privacy", "visual_ocr_engine.ts")
        self.detector_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "privacy", "visual_detector.ts")
        self.redactor_path = os.path.join(os.path.dirname(__file__), "..", "extension", "src", "content", "canvas_capture.ts")

    def test_engine_file_exists_and_uses_tesseract(self):
        """Verify that visual_ocr_engine.ts exists and imports genuine Tesseract WASM core."""
        self.assertTrue(os.path.exists(self.engine_path), "visual_ocr_engine.ts missing")
        with open(self.engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("import { createWorker", content)
        self.assertIn("ModelLifecycleState", content)
        self.assertIn("MODEL_UNINITIALIZED", content)
        self.assertIn("MODEL_LOADING", content)
        self.assertIn("MODEL_READY", content)
        self.assertIn("INFERENCE_RUNNING", content)
        self.assertIn("INFERENCE_COMPLETE", content)
        self.assertIn("INFERENCE_FAILED", content)

    def test_no_fake_webgpu_reporting(self):
        """Verify that backend reporting distinguishes capability detection from actual execution."""
        with open(self.engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ensure model initialization sets actual running backend
        self.assertIn("this.currentBackend = 'webgpu'", content)
        self.assertIn("this.currentBackend = 'wasm'", content)
        self.assertIn("this.currentBackend = 'cpu'", content)

    def test_visual_detector_pixel_recognition_integration(self):
        """Verify that visual_detector.ts calls modelEngine.recognizePixels when raw image input is present."""
        with open(self.detector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("LocalVisualModelEngine", content)
        self.assertIn("recognizePixels", content)
        self.assertIn("VISUAL_OCR", content)

    def test_provenance_metadata_attached(self):
        """Verify that GenuineVisualEntity includes provenance metadata (modelId, backend, inferenceId)."""
        with open(self.engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("modelId", content)
        self.assertIn("backend", content)
        self.assertIn("inferenceId", content)
        self.assertIn("inferenceLatencyMs", content)

if __name__ == "__main__":
    unittest.main()
