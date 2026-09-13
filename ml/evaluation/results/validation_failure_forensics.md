# Gate 1 — Validation Forensic Failure Report

## Summary
- **Total Validation Scenes**: 30
- **Total Ground-Truth Objects**: 575

## Failure Category Breakdown

| Category Code | Description | Count | Percentage |
| :--- | :--- | :--- | :--- |
| **G_correct_detection** | Detected (IoU >= 0.50, Conf >= 0.30, Correct Class) | 47 | 8.17% |
| **A_representation_loss** | Spatial resolution collapse (<16px max dim) | 0 | 0.00% |
| **B_low_confidence** | IoU >= 0.50 but confidence < 0.30 | 7 | 1.22% |
| **C_wrong_class** | IoU >= 0.50 but category predicted incorrectly | 75 | 13.04% |
| **D_localization_failure** | Candidate near GT (0.15 <= IoU < 0.50) | 364 | 63.30% |
| **F_grid_collision** | No candidate near GT (IoU < 0.15) | 82 | 14.26% |

## Size Bucket Breakdown

| Bucket | Count | Percentage |
| :--- | :--- | :--- |
| <8px | 0 | 0.00% |
| 8-16px | 0 | 0.00% |
| 16-32px | 100 | 17.39% |
| 32-64px | 24 | 4.17% |
| 64-128px | 93 | 16.17% |
| >128px | 358 | 62.26% |
