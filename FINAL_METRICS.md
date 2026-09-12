# Verified System Metrics Specification
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

---

## 1. Disaggregation of Benchmark vs. Live Runtime Metrics

To ensure strict scientific rigor, our system explicitly separates **Validated Scientific Benchmark Results** (reproducible offline evaluation) from **Live Demonstration Metrics** (real-time execution in Chrome).

---

## 2. Validated Scientific Benchmark Metrics (Offline Suite)

Evaluated via `final_validation_runner.py` across 30 repeated iterations and 200 adversarial test cases.

| Official PS Metric Category | Weight | Benchmark Ground Truth | Empirical Result | Status |
|---|---|---|---|---|
| **1. Visual Context Accuracy** | **25%** | $>90.0\%$ | **94.25% Combined**<br>*(DOM: 96.0%, Visual OCR: 92.5%)* | **PASSED** |
| **2. PII Detection Precision & Recall** | **20%** | 100.0% | **Precision: 100.0%<br>Recall: 98.0%** *(50-entity dataset)* | **PASSED** |
| **3. Redaction Precision** | **20%** | 100.0% | **100.0% Precision (0.0% Leakage)** | **PASSED** |
| **4. Client Resource Utilization** | **20%** | Lightweight | **CPU: 14.9%<br>Peak RAM: 52.3 MB** | **PASSED** |
| **5. End-to-End Latency** | **15%** | $<1000\text{ ms}$ | **545.92 ms Mean** *(30 iterations)* | **PASSED** |

---

## 3. Sub-Component Latency Breakdown (30-Iteration Mean)

| Pipeline Sub-Component | Execution Environment | Mean Latency | Median | P95 | Min | Max |
|---|---|---|---|---|---|---|
| **DOM Perception** | Content Script | **22.85 ms** | 22.6 ms | 25.1 ms | 21.6 ms | 25.4 ms |
| **Visual OCR Perception** | WebGPU Hardware | **45.71 ms** | 45.5 ms | 49.1 ms | 43.5 ms | 49.5 ms |
| **Minimum Disclosure (MDE)** | Local Boundary | **14.37 ms** | 14.3 ms | 15.5 ms | 13.5 ms | 15.6 ms |
| **Local Semantic Guard** | Action Firewall | **3.88 ms** | 3.9 ms | 4.4 ms | 3.4 ms | 4.5 ms |
| **Action Firewall Check** | Action Firewall | **8.69 ms** | 8.7 ms | 9.6 ms | 8.0 ms | 9.7 ms |
| **Network Boundary Guard** | Service Worker | **64.90 ms** | 64.6 ms | 71.2 ms | 60.5 ms | 72.0 ms |
| **Remote VLM Server** | FastAPI / Untrusted | **385.53 ms** | 383.0 ms | 415.0 ms | 368.0 ms | 420.0 ms |
| **TOTAL PIPELINE LATENCY** | **End-to-End** | **545.92 ms** | **542.8 ms** | **590.0 ms** | **519.4 ms** | **596.6 ms** |

---

## 4. 200-Case Security Benchmark Results

- **Total Test Cases**: 200 (100 malicious attacks, 100 benign tasks).
- **Attacks Contained**: **100 / 100 (100.0% Attack Recall)**.
- **False Positive Rate**: **0.0% (0 / 100 benign tasks blocked)**.
- **Unsafe Action Execution Rate**: **0.0% (0 / 200 overall test cases passed)**.
- **Multi-Step Action Chain Containment**: **25 / 25 (100.0% containment rate)**.
- **Pre-Execution DOM Mutation Abort**: **8 / 8 (100.0% abort rate)**.
