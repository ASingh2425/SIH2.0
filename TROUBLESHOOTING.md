# Demonstration & Runtime Troubleshooting Guide
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

---

## 1. Quick Recovery Matrix

| Issue Symptom | Root Cause | Instant Recovery Action |
|---|---|---|
| **Extension fails to load in Chrome** | `extension/dist/` build missing or stale | Run `cd extension && npm run build`, then click **Reload** in `chrome://extensions`. |
| **Side panel shows "Disconnected"** | Content script not injected in tab | Refresh active tab (`sih_demo_scenario.html`) or reopen Side Panel. |
| **Server connection refused (`localhost:8000`)** | FastAPI backend server not started | Open terminal, run `python server/main.py`. Verify `http://localhost:8000/health`. |
| **Network request fails with HTTP 400** | Egress guard detected raw PII in payload | Check entity sensitivity mappings; MDE automatically redacts raw secrets (`zeroRawPIIVerified`). |
| **Action firewall blocks legitimate action** | Task ID mismatch or origin domain mismatch | Click **Reset Task** in Side Panel to re-initialize `IntentAnchor`. |

---

## 2. Common Debug Commands

### Re-build Chrome Extension:
```bash
cd extension
npm run build
```

### Test Remote Reasoner API Health:
```bash
curl http://localhost:8000/health
```

### Run Benchmark Suite:
```bash
cd benchmark
python final_validation_runner.py
```
