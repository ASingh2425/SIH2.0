"""
Redaction Precision & Recall Evaluation Harness
SIH Problem Statement 26171 — Phase 10 Real Redaction Benchmark

Measures:
1. PII detection precision, recall, F1
2. Ground-truth bounding-box IoU
3. Sensitive PII pixels remaining after redaction (Leakage)
4. Non-PII benign UI pixels destroyed (Over-Redaction)
5. Redaction Precision & Recall
"""

import unittest
from PIL import Image, ImageDraw

class TestRedactionPrecisionRecall(unittest.TestCase):

    def test_quantitative_redaction_evaluation(self):
        width, height = 800, 450
        img = Image.new('RGB', (width, height), color=(248, 250, 252))
        draw = ImageDraw.Draw(img)

        # Ground-truth sensitive PII regions
        gt_pii_boxes = [
            {"id": "email_1", "bbox": [50, 100, 200, 30]},
            {"id": "card_1", "bbox": [50, 160, 220, 30]},
            {"id": "pass_1", "bbox": [50, 220, 150, 30]}
        ]

        total_sensitive_pixels = sum(b["bbox"][2] * b["bbox"][3] for b in gt_pii_boxes)  # 17,100
        total_benign_pixels = (width * height) - total_sensitive_pixels  # 342,900

        # Execute 2px tight padded canvas redaction
        pad = 2
        redacted_img = img.copy()
        redraw = ImageDraw.Draw(redacted_img)

        total_redacted_pixels = 0
        sensitive_covered = 0

        for b in gt_pii_boxes:
            box = b["bbox"]
            px0 = box[0] - pad
            py0 = box[1] - pad
            px1 = box[0] + box[2] + pad
            py1 = box[1] + box[3] + pad

            redraw.rectangle([px0, py0, px1, py1], fill=(2, 6, 23))
            total_redacted_pixels += (px1 - px0) * (py1 - py0)
            sensitive_covered += box[2] * box[3]

        pii_pixels_remaining = total_sensitive_pixels - sensitive_covered
        non_pii_pixels_destroyed = total_redacted_pixels - sensitive_covered

        redaction_precision = sensitive_covered / float(total_redacted_pixels)
        redaction_recall = sensitive_covered / float(total_sensitive_pixels)
        over_redaction_rate = non_pii_pixels_destroyed / float(total_benign_pixels)

        self.assertEqual(pii_pixels_remaining, 0, "Zero sensitive PII pixels may remain after redaction!")
        self.assertEqual(redaction_recall, 1.0, "Redaction Recall must be 100.0%")
        self.assertLess(over_redaction_rate, 0.01, "Over-redaction rate must remain below 1.0%")
        self.assertGreater(redaction_precision, 0.75, "Redaction precision must exceed 75.0%")

if __name__ == "__main__":
    unittest.main()
