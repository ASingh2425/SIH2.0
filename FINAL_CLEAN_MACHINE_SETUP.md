# FINAL CLEAN MACHINE SETUP GUIDE — SIH PROBLEM STATEMENT 26171
## Reproducible Deployment & Environment Setup Instructions

> **REVISION**: 1.0 (POST-REHEARSAL AUDITED STATE)  
> **PURPOSE**: Comprehensive, zero-memory-dependency deployment guide allowing any judge, evaluator, or developer to build, install, configure, and execute the browser agent extension on a fresh clean machine.

---

### SECTION 1: PREREQUISITE ENVIRONMENT REQUIREMENTS

| DEPENDENCY | REQUIRED VERSION | VERIFICATION COMMAND | PURPOSE |
| :--- | :--- | :--- | :--- |
| **Node.js** | `>= 18.0.0` (Tested: `v22.17.0`) | `node -v` | JavaScript/TypeScript build runtime & Vite bundler |
| **npm** | `>= 9.0.0` (Tested: `11.6.2`) | `npm -v` | Package manager for extension build dependencies |
| **Python** | `>= 3.10` (Tested: `3.13.5`) | `python --version` | Benchmark test suite runner & local HTTP fixture server |
| **Pillow (PIL)** | `>= 9.0.0` | `python -c "import PIL"` | Image generation & canvas pixel comparison in benchmarks |
| **Chrome Browser** | `>= 115.0` (Chromium Manifest V3) | Chrome Menu -> About | Extension execution runtime (`chrome.tabs.captureVisibleTab`) |

---

### SECTION 2: CLEAN INSTALLATION PROCEDURE

#### Step 1: Clone / Copy Repository
```bash
cd c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0
```

#### Step 2: Install Extension Build Dependencies
```bash
cd extension
npm install
```

#### Step 3: Build the Chrome Extension Bundle
```bash
npm run build
```
* **Expected Build Output**:
  - `dist/index.html` (~0.49 kB)
  - `dist/assets/main-*.css` (~15 kB)
  - `dist/background.js` (~3.93 kB)
  - `dist/content.js` (~65.78 kB)
  - `dist/assets/main-*.js` (~177 kB)
  - `dist/manifest.json` (Copied from root)

#### Step 4: Launch Local HTTP Server for Demo Fixtures
Open a separate terminal window at repository root:
```bash
cd c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0
python -m http.server 8000
```

---

### SECTION 3: CHROME EXTENSION INSTALLATION & CONFIGURATION

1. Open Google Chrome.
2. Navigate to `chrome://extensions/`.
3. Enable the **Developer mode** toggle switch in the top-right corner.
4. Click **Load unpacked** in the top-left toolbar.
5. Select the directory: `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0\extension\dist`.
6. Confirm the extension loads with:
   - **Name**: `SIH Lightweight Visual Browser Agent Extension`
   - **Version**: `1.0.0`
   - **Manifest Version**: `3`
   - **Permissions Requested**: `activeTab`, `scripting`, `storage`, `tabs`

---

### SECTION 4: REQUIRED ASSETS & NETWORK ACCESSIBILITY

| ASSET | ORIGIN / LOCATION | INITIAL RUN BEHAVIOR | SUBSEQUENT RUN BEHAVIOR |
| :--- | :--- | :--- | :--- |
| **WASM Core Binary** | `tesseract-core.wasm` (CDN) | Downloaded over HTTPS on 1st execution pass | Cached locally in browser **IndexedDB** & Worker Cache |
| **Language Weights** | `eng.traineddata.gz` (CDN) | Downloaded over HTTPS on 1st execution pass | Cached locally in browser **IndexedDB** & Worker Cache |
| **Demo Fixture HTML** | `http://localhost:8000/` | Served locally via Python `http.server` | Served locally via Python `http.server` |
| **Remote Reasoner** | `http://localhost:8000/api/v1/reason` | Optional mock local server or external LLM API | Optional mock local server or external LLM API |

---

### SECTION 5: CLEAN-MACHINE VERIFICATION RUN

Run the automated verification suite to confirm the environment is correctly configured:

```bash
python -m unittest discover -s benchmark
```

* **Expected Result**: `Ran 17 tests in ~0.04s - OK` with 100% precision & recall metrics.

---

> **END OF CLEAN MACHINE SETUP GUIDE**
