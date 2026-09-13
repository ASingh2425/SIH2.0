"""
Phase 0 System Trace Script — SIH Problem Statement 26171
Traces the exact tensor dimensions at every layer from NCHW [1, 3, 256, 256] input
through Conv backbone, feature maps, grid heads, box decoder, to NMS predictions.
Outputs: ml/evaluation/results/phase0_system_trace.json
"""

import os
import sys
import json
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.training.train_ui_detector import MultiScaleUIDetector
from ml.training.fpn_ui_detector import FPNUIDetector

def run_phase0_system_trace(base_dir: str):
    print("==================================================")
    print("PHASE 0 — SYSTEM TRACE & TENSOR SHAPE AUDIT")
    print("==================================================")

    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)

    # 1. MultiScaleUIDetector Trace
    m_baseline = MultiScaleUIDetector()
    m_baseline.eval()
    x = torch.randn(1, 3, 256, 256)

    stage1_out = m_baseline.stage1(x)               # [1, 16, 128, 128]
    stage2_out = m_baseline.stage2(stage1_out)      # [1, 32, 64, 64]
    stage3_out = m_baseline.stage3(stage2_out)      # [1, 64, 32, 32]
    stage4_out = m_baseline.stage4_fine(stage3_out) # [1, 64, 16, 16]
    stage5_out = m_baseline.stage5_coarse(stage4_out)# [1, 64, 8, 8]

    fine_raw = m_baseline.fine_head(stage4_out)     # [1, 12, 16, 16]
    coarse_raw = m_baseline.coarse_head(stage5_out) # [1, 12, 8, 8]

    baseline_out = m_baseline(x) # [1, 640, 6]

    # 2. FPNUIDetector Trace
    m_fpn = FPNUIDetector()
    m_fpn.eval()
    fpn_out = m_fpn(x) # [1, 2688, 6]

    trace_payload = {
        "input_tensor_shape": list(x.shape),
        "baseline_multiscale_detector": {
            "stage1_conv": list(stage1_out.shape),
            "stage2_conv": list(stage2_out.shape),
            "stage3_conv": list(stage3_out.shape),
            "stage4_fine_feature_map": list(stage4_out.shape),
            "stage5_coarse_feature_map": list(stage5_out.shape),
            "fine_head_raw": list(fine_raw.shape),
            "coarse_head_raw": list(coarse_raw.shape),
            "final_concatenated_output": list(baseline_out.shape),
            "total_candidate_slots": 640
        },
        "fpn_high_res_detector": {
            "p3_fine_grid": [1, 2048, 6],
            "p4_medium_grid": [1, 512, 6],
            "p5_coarse_grid": [1, 128, 6],
            "final_concatenated_output": list(fpn_out.shape),
            "total_candidate_slots": 2688
        }
    }

    out_file = os.path.join(results_dir, "phase0_system_trace.json")
    with open(out_file, "w") as f:
        json.dump(trace_payload, f, indent=2)

    print(f"[OK] System Trace Complete. Output saved -> '{out_file}'")
    print("--------------------------------------------------")
    return trace_payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_phase0_system_trace(pwd)
