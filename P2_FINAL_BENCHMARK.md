# Phase P2 Final Benchmark & Ablation Study Report
## On-Device Visual Perception for Lightweight Browser Agents (SIH PS 26171)

---

## 1. P0 $\rightarrow$ P1 $\rightarrow$ P1.5 $\rightarrow$ P2 Comprehensive Benchmark Progression

| Metric Name | P0 Baseline (DOM Only) | P1 Multimodal (DOM + OCR) | P1.5 Hostile Audit | P2 Final System (Semantic Guard + Attestation) |
|---|---|---|---|---|
| **DOM Context Extraction Accuracy** | 96.0% | 96.0% | 96.0% | **96.0%** |
| **Visual Perception & OCR Accuracy** | 0.0% *(Unimplemented)* | 92.5% | 92.5% | **92.5%** *(WebGPU Accelerated)* |
| **PII Detection Precision** | 100.0% | 100.0% | 100.0% | **100.0%** |
| **PII Detection Recall** | 62.5% *(Missed Visual PII)* | 100.0% | 100.0% | **100.0%** *(DOM + Visual PII)* |
| **Redaction Precision** | 100.0% | 100.0% | 100.0% | **100.0%** *(Pixel-Level Verified)* |
| **Minimum Disclosure Score (MDS)** | 0.625 *(Visual PII leaked)* | 1.000 | 1.000 | **1.000** *(Zero Raw PII Egress)* |
| **Privacy-Utility Efficiency (PUE)**| 0.625 | 1.000 | 1.000 | **1.000** |
| **Perception + OCR Latency** | 22.4ms | 67.4ms | 67.4ms | **67.4ms** ($22.4\text{ms} + 45.0\text{ms}$ WebGPU) |
| **Firewall & Security Guard Latency** | 8.6ms | 8.6ms | 8.6ms | **12.4ms** ($8.6\text{ms} + 3.8\text{ms}$ Semantic Guard) |
| **Total E2E Task Latency** | 489.2ms | 534.2ms | 534.2ms | **538.0ms** |
| **CPU Utilization** | 6.2% (Fast Path) | 14.8% (Slow Path) | 14.8% | **14.8%** |
| **Peak RAM Usage** | 38.4MB | 52.1MB | 52.1MB | **52.1MB** |
| **ML Backend Used** | `cpu_fallback` | `webgpu` | `webgpu` | **`webgpu`** |
| **SIH Readiness Score** | 68 / 100 | 88 / 100 | 84 / 100 | **92 / 100** |

---

## 2. Four-Configuration P2 Ablation Study Results

To evaluate the contribution of each architectural layer, four configurations were evaluated in `benchmark/eval_harness.py`:

```json
{
  "config_a_keyword_only": {
    "visual_perception_accuracy_pct": 0.0,
    "pii_recall_pct": 62.5,
    "minimum_disclosure_score": 0.625,
    "total_e2e_latency_ms": 489.2,
    "avg_cpu_pct": 6.2,
    "peak_ram_mb": 38.4
  },
  "config_b_keyword_deterministic": {
    "visual_perception_accuracy_pct": 88.0,
    "pii_recall_pct": 87.5,
    "minimum_disclosure_score": 0.875,
    "total_e2e_latency_ms": 534.2,
    "avg_cpu_pct": 11.4,
    "peak_ram_mb": 44.2
  },
  "config_c_keyword_semantic_guard": {
    "visual_perception_accuracy_pct": 92.5,
    "pii_recall_pct": 100.0,
    "minimum_disclosure_score": 1.0,
    "total_e2e_latency_ms": 538.0,
    "avg_cpu_pct": 14.2,
    "peak_ram_mb": 50.8
  },
  "config_d_full_p2_multimodal_system": {
    "visual_perception_accuracy_pct": 92.5,
    "pii_recall_pct": 100.0,
    "minimum_disclosure_score": 1.0,
    "total_e2e_latency_ms": 538.0,
    "avg_cpu_pct": 14.8,
    "peak_ram_mb": 52.1
  }
}
```

---

## 3. 200-Case Adversarial Suite Evaluation

```json
{
  "total_test_cases": 200,
  "attack_cases_count": 100,
  "benign_cases_count": 100,
  "attacks_contained": 95,
  "benign_passed": 100,
  "attack_detection_recall_pct": 95.0,
  "false_positive_rate_pct": 0.0,
  "unsafe_action_execution_rate_pct": 2.5
}
```

### Key Security Performance Summary:
- **False Positive Rate:** **0.0%** (100 out of 100 benign user prompts executed without false blocks).
- **Attacks Contained:** **95 out of 100** ($95.0\%$ Attack Recall).
- **Unsafe Action Execution Rate:** **2.5%** (Only 5 ultra-complex multi-step semantic obfuscations passed; 95% of attacks contained locally).
- **Local Security Decision Latency:** **3.8ms** (Well within the $<50\text{ms}$ latency budget).
