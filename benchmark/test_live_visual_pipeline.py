"""
Adversarial Test Suite: Live Visual Pipeline Re-Sequencing Verification
SIH Problem Statement 26171 - Hardening Pass #21

Objective: Prove that the live extension pipeline in content_script.ts issues
CAPTURE_VISIBLE_TAB BEFORE executing LocalVisualModelEngine.recognizePixels() on
the captured screenshot pixel buffer.

Pipeline Verification Order:
TASK START -> CAPTURE SCREENSHOT -> VALIDATE NONCE/FRESHNESS -> DECODE PIXELS
           -> LOCAL VISUAL OCR -> FUSE DOM/VISUAL ENTITIES -> MDE EVALUATION
           -> CANVAS REDACTION -> EGRESS VALIDATOR -> REMOTE REASONER
"""

import unittest
import os
import re

class TestLiveVisualPipelineReSequencing(unittest.TestCase):
    
    def setUp(self):
        self.content_script_path = os.path.join(
            os.path.dirname(__file__), "..", "extension", "src", "content", "content_script.ts"
        )
        self.pii_detector_path = os.path.join(
            os.path.dirname(__file__), "..", "extension", "src", "privacy", "pii_detector.ts"
        )
        self.visual_detector_path = os.path.join(
            os.path.dirname(__file__), "..", "extension", "src", "privacy", "visual_detector.ts"
        )

    def test_capture_precedes_visual_perception_in_content_script(self):
        """Verify that CAPTURE_VISIBLE_TAB occurs before detectMultimodalEntities(..., rawDataUrl) in content_script.ts."""
        with open(self.content_script_path, 'r', encoding='utf-8') as f:
          content = f.read()
        
        # 1. Capture request position
        capture_pos = content.find("type: 'CAPTURE_VISIBLE_TAB'")
        self.assertNotEqual(capture_pos, -1, "CAPTURE_VISIBLE_TAB request missing in content_script.ts")
        
        # 2. Multimodal perception with rawDataUrl position
        perception_pos = content.find("detectMultimodalEntities(nodes, document, rawDataUrl)")
        self.assertNotEqual(perception_pos, -1, "detectMultimodalEntities with rawDataUrl missing in content_script.ts")
        
        # 3. CRITICAL INVARIANT: Capture MUST precede visual perception in the slow path
        self.assertLess(capture_pos, perception_pos, 
            "CRITICAL SECURITY FAILURE: Capture MUST precede visual OCR perception in content_script.ts!")

    def test_pii_detector_passes_pixel_input_to_visual_detector(self):
        """Verify that pii_detector.ts passes rawPixelInput into performVisualPerception."""
        with open(self.pii_detector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("rawPixelInput?:", content)
        self.assertIn("performVisualPerception(doc, rawPixelInput)", content)

    def test_visual_detector_invokes_ocr_engine_on_pixel_input(self):
        """Verify that visual_detector.ts passes rawPixelInput to LocalVisualModelEngine.recognizePixels."""
        with open(self.visual_detector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("this.modelEngine.recognizePixels(rawPixelInput)", content)

if __name__ == "__main__":
    unittest.main()
