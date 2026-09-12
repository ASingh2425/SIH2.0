# Build Reproduction & Engineering Baseline Guide
## Tag: `SIH-P26171-FINAL-ENGINEERING-BASELINE`
### SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

---

## 1. Baseline Engineering Inventory

This document records the exact state, dependency versions, component locations, and step-by-step reproduction instructions for Git checkpoint/tag **`SIH-P26171-FINAL-ENGINEERING-BASELINE`**.

### Component & Source Inventory
- **Chrome Extension Source**: [`extension/src/`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/) (Manifest V3, React 18.3.1, TypeScript 5.7.2, Vite 6.0.5)
- **Untrusted Remote VLM Server**: [`server/main.py`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/server/main.py) (FastAPI 0.115.0+, Uvicorn 0.30.0+, Pydantic 2.8.0+)
- **Benchmark Suite & Harness**: [`benchmark/final_validation_runner.py`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/benchmark/final_validation_runner.py)
- **Adversarial Benchmark Dataset**: [`benchmark/adversarial_prompt_injection_200.json`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/benchmark/adversarial_prompt_injection_200.json) (200 cases: 100 attacks, 100 benign)
- **Official SIH Reports**:
  - [`FINAL_CLAIM_AUDIT.md`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_CLAIM_AUDIT.md)
  - [`FINAL_VALIDATION_REPORT.md`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_VALIDATION_REPORT.md)
  - [`FINAL_SECURITY_LIMITATIONS.md`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_SECURITY_LIMITATIONS.md)
  - [`FINAL_SIH_JUDGE_QA.md`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_SIH_JUDGE_QA.md)
- **System Documentation**: [`README.md`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/README.md) & [`walkthrough.md`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/walkthrough.md)

---

## 2. Environment & Dependency Versions

### Local Runtime Environment
- **Operating System**: Windows / Linux / macOS (Chrome Extension platform)
- **Node.js Runtime**: `v22.17.0` (Minimum: `v18.0.0`)
- **Package Manager**: `npm 11.6.2` (Minimum: `npm 9.0.0`)
- **Python Runtime**: `3.13.5` (Minimum: `Python 3.10+`)
- **Target Browser**: Google Chrome 120+ (Manifest V3 support + WebGPU enabled)

### Node.js Package Versions (`extension/package.json`)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.469.0"
  },
  "devDependencies": {
    "@types/chrome": "^0.0.280",
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.7.2",
    "vite": "^6.0.5"
  }
}
```

### Python Package Versions (`server/requirements.txt`)
```text
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.8.0
python-dotenv>=1.0.1
requests>=2.32.0
```

### Model & Hardware Acceleration Hierarchy
1. **Primary GPU Backend**: WebGPU Hardware Acceleration (`ONNX-ViT-MobileNetV4-OCR-WebGPU`, 45ms latency)
2. **Secondary WASM Backend**: WebAssembly Engine (`Transformers.js-ONNX-WASM-v3`, 145ms latency)
3. **Tertiary CPU Fallback**: Deterministic Canvas Engine (`Canvas2D-Deterministic-OCR-Engine`, 290ms latency)

---

## 3. Step-by-Step Build & Reproduction Guide

Follow these exact steps to set up, build, execute, and verify the baseline system.

### Step 1: Install Dependencies

#### A. Install Chrome Extension Dependencies:
```bash
cd extension
npm install
```

#### B. Install Python Server Dependencies:
```bash
cd ../server
pip install -r requirements.txt
```

---

### Step 2: Build the Chrome Extension

Compile the TypeScript and React source files into the production Manifest V3 bundle (`extension/dist/`):

```bash
cd ../extension
npm run build
```

**Expected Output:**
```
vite v6.0.5 building for production...
✓ 142 modules transformed.
dist/manifest.json              0.45 kB
dist/background/service_worker.js 14.20 kB
dist/content/content_script.js   28.40 kB
dist/ui/sidepanel.html           0.85 kB
dist/ui/sidepanel.js            184.20 kB
✓ built in 1.48s
```

---

### Step 3: Start Remote Reasoning Server

Launch the FastAPI backend server on port 8000:

```bash
cd ../server
python main.py
```

**Expected Output:**
```
INFO:     Started server process [PID 12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### Step 4: Load Extension in Google Chrome

1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Toggle **Developer mode** in the top right corner to **ON**.
3. Click the **Load unpacked** button in the top left.
4. Select the `extension/dist/` directory inside your project folder.
5. Verify that **"On-Device Privacy Browser Agent - SIH PS 26171"** appears in your extension list with Manifest V3 enabled.

---

### Step 5: Execute Programmatic Benchmark Suite

Run the automated programmatic benchmark suite to evaluate latency, PII detection precision, ablation configs, and security containment:

```bash
cd ../benchmark
python final_validation_runner.py
```

---

### Step 6: Verify Reported Baseline Metrics

Compare the output from `final_validation_runner.py` against the ground-truth benchmark targets in [`FINAL_VALIDATION_REPORT.md`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/FINAL_VALIDATION_REPORT.md):

| Target Metric | Baseline Expected Result | Status Verification Criteria |
|---|---|---|
| **DOM Context Accuracy** | **96.0%** | Equal to 96.0% on `sih_demo_scenario.html` |
| **Visual Perception OCR Accuracy** | **92.5%** | Equal to 92.5% on canvas/SVG targets |
| **Combined Multimodal Accuracy** | **94.25%** | Combined score matches 94.25% |
| **PII Detection Precision & Recall** | **100% / 100%** | Zero false positives / zero false negatives |
| **Redaction Precision** | **100.0% (0.0% Leakage)** | Verified by `redaction_validator.py` |
| **End-to-End Latency** | **538.0 ms Mean** | Within $\pm 30\text{ ms}$ of 538.0ms over 30 runs |
| **Attack Detection Recall** | **95.0%** | 95 / 100 attacks contained in 200-case suite |
| **False Positive Rate** | **0.0%** | 100 / 100 benign tasks executed cleanly |
| **Unsafe Action Execution Rate** | **2.5%** | Exactly 5 / 200 total cases passed |
