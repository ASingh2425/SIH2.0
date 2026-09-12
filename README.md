# On-Device Visual Perception for Lightweight Browser Agents (SIH PS 26171)

## Overview
This repository contains a privacy-preserving browser agent built for **Smart India Hackathon (SIH) Problem Statement 26171**.

The fundamental security principle is:
> **"THE CLOUD CAN REASON ABOUT THE TASK, BUT THE DEVICE DECIDES WHAT IT IS ALLOWED TO SEE AND WHAT IT IS ALLOWED TO DO."**

---

## Key Architecture & Features

1. **Client-Side Visual Perception & OCR:** Client-side visual perception engine (`visual_detector.ts`) supporting **WebGPU**, **WASM**, and **CPU fallback** backends. Processes text regions inside `<canvas>`, `<svg>`, `<img>`, and visually rendered elements.
2. **Local Client Screenshot Canvas Redactor:** Obfuscates sensitive visual bounding boxes directly on HTML5 Canvas on the client before network egress (`#020617` solid fill).
3. **Task-Aware Minimum Disclosure Engine (MDE):** Evaluates entity sensitivity vs. task necessity (`KEEP`, `TOKENIZE`, `MASK`, `REMOVE`).
4. **Local Ephemeral Token Vault:** Short-lived, task/origin-scoped token mappings (`PERSON#A72F` $\rightarrow$ `John Smith`).
5. **Network Privacy Attestation:** Independent Service Worker egress guard validating zero raw PII egress (`PrivacyBoundaryReport`).
6. **Local Action Firewall & Semantic Guard:** Enforces immutable `IntentAnchor`, local semantic analysis, risk scoring (`LOW` to `CRITICAL`), origin checks, and prompt injection containment.

---

## Official SIH Final Deliverable Reports

- [FINAL_CLAIM_AUDIT.md](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_CLAIM_AUDIT.md): Line-by-line Code-to-Claim Audit tracing all documentation claims to exact source code lines.
- [FINAL_VALIDATION_REPORT.md](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_VALIDATION_REPORT.md): 30-iteration latency statistics, 50-entity PII benchmark results, 5-config ablation study, and official SIH metric table.
- [FINAL_SECURITY_LIMITATIONS.md](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_SECURITY_LIMITATIONS.md): Transparent security limitations document detailing the 5 failed attack cases (2.5% unsafe execution rate), root causes, security layer failures, and mitigations.
- [FINAL_SIH_JUDGE_QA.md](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_SIH_JUDGE_QA.md): 30 evidence-backed answers to technical judge questions covering all core domains of SIH PS 26171.

---

## Directory Structure

```
SIH_2.0/
├── extension/               # Chrome Extension (Manifest V3 + Vite + React + TypeScript)
│   ├── manifest.json
│   ├── src/
│   │   ├── background/     # Service Worker & Network Privacy Attestation
│   │   ├── content/        # DOM Extractor, Action Executor & Canvas Redactor
│   │   ├── privacy/        # LocalPIIDetector, LocalVisualDetector, MDE, Token Vault
│   │   ├── firewall/       # Local Action Firewall & Intent Anchor
│   │   ├── ui/             # Side Panel Dashboard UI (5 Live Diagnostic Tabs)
│   │   └── types/          # Shared Interface Contracts
├── server/                 # Untrusted Remote VLM Server (Python FastAPI)
│   ├── main.py
│   └── app/
│       ├── schema/         # Pydantic JSON Action Protocols
│       └── vlm_agent.py    # Sanitized Context VLM Planner
├── benchmark/              # Evaluation & Benchmark Suite
│   ├── test_pages/         # Flight Booking & Visual-Only PII Test Pages
│   ├── final_validation_runner.py # Reproducible 30-Iteration Latency & 200-Case Security Benchmark
│   ├── metrics_calculator.py   # Empirical Metric Calculator
│   └── adversarial_prompt_injection_200.json # 200-Case Adversarial Suite
├── FINAL_CLAIM_AUDIT.md
├── FINAL_VALIDATION_REPORT.md
├── FINAL_SECURITY_LIMITATIONS.md
└── FINAL_SIH_JUDGE_QA.md
```

---

## Reproducibility & Benchmark Execution

### 1. Build Chrome Extension:
```bash
cd extension
npm run build
```

### 2. Run Final Programmatic Benchmark Suite:
```bash
cd benchmark
python final_validation_runner.py
```

### 3. Start Remote Reasoning Server:
```bash
cd server
python main.py
```
Server active at `http://localhost:8000`.
