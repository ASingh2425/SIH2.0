import { useState } from 'react';
import { Shield, Play, AlertTriangle, CheckCircle, XCircle, Cpu, Image as ImageIcon } from 'lucide-react';
import { CompleteAuditLedger } from '../types/ledger';

export default function SidePanel() {
  const [activeTab, setActiveTab] = useState<'perception' | 'privacy' | 'agent' | 'performance' | 'audit'>('agent');
  const [userPrompt, setUserPrompt] = useState('Book cheapest flight from Delhi to Mumbai tomorrow');
  const [forceSlowPath, setForceSlowPath] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [ledgerData, setLedgerData] = useState<CompleteAuditLedger | null>(null);
  const [lastResponse, setLastResponse] = useState<any>(null);

  const handleStartTask = async () => {
    setIsRunning(true);
    const taskId = `task_${Date.now()}`;

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab?.id) {
        chrome.tabs.sendMessage(
          tab.id,
          { type: 'START_TASK', userPrompt, taskId, forceSlowPath },
          (response) => {
            setIsRunning(false);
            if (response) {
              setLastResponse(response);
              fetchLedger(taskId, tab.id);
            }
          }
        );
      } else {
        setIsRunning(false);
      }
    } catch (_e) {
      setIsRunning(false);
    }
  };

  const fetchLedger = (taskId: string, tabId?: number) => {
    if (tabId) {
      chrome.tabs.sendMessage(tabId, { type: 'GET_LEDGER_DATA', taskId }, (data) => {
        if (data) setLedgerData(data);
      });
    }
  };

  const handleConfirmAction = async () => {
    if (!lastResponse?.candidateAction || !lastResponse?.firewallResult) return;
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.id) {
      chrome.tabs.sendMessage(
        tab.id,
        {
          type: 'EXECUTE_CONFIRMED_ACTION',
          action: lastResponse.candidateAction,
          firewallResult: lastResponse.firewallResult,
        },
        (res) => {
          alert(res.message || 'Action executed successfully');
        }
      );
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 p-4 border-l border-slate-800">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-emerald-400" />
          <div>
            <h1 className="font-bold text-sm text-slate-100 tracking-wide">PRIVACY GUARD AGENT</h1>
            <p className="text-[10px] text-slate-400 font-mono">SIH PS 26171 | MULTIMODAL P1</p>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          FAIL-CLOSED
        </span>
      </div>

      {/* Task Controller Input */}
      <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 mb-3">
        <label className="block text-[11px] font-semibold text-slate-300 mb-1">CURRENT USER TASK</label>
        <textarea
          value={userPrompt}
          onChange={(e) => setUserPrompt(e.target.value)}
          rows={2}
          className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
          placeholder="Enter user goal e.g., Book flight from Delhi to Mumbai"
        />

        <div className="flex items-center gap-2 mt-2">
          <input
            type="checkbox"
            id="slowPathToggle"
            checked={forceSlowPath}
            onChange={(e) => setForceSlowPath(e.target.checked)}
            className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-0"
          />
          <label htmlFor="slowPathToggle" className="text-[10px] text-slate-300 font-mono">
            Enable Visual Perception & Canvas Redaction
          </label>
        </div>

        <button
          onClick={handleStartTask}
          disabled={isRunning}
          className="mt-2 w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-slate-950 font-bold text-xs rounded flex items-center justify-center gap-1 transition"
        >
          {isRunning ? <span className="animate-spin">⏳</span> : <Play className="w-3.5 h-3.5 fill-current" />}
          {isRunning ? 'PERCEIVING & REASONING...' : 'RUN PRIVACY GUARD AGENT'}
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 mb-3 text-xs gap-1 font-mono">
        <button
          onClick={() => setActiveTab('agent')}
          className={`flex-1 py-1 text-center rounded-t border-b-2 transition ${
            activeTab === 'agent'
              ? 'border-emerald-400 text-emerald-400 bg-slate-900'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          AGENT
        </button>
        <button
          onClick={() => setActiveTab('privacy')}
          className={`flex-1 py-1 text-center rounded-t border-b-2 transition ${
            activeTab === 'privacy'
              ? 'border-emerald-400 text-emerald-400 bg-slate-900'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          PRIVACY
        </button>
        <button
          onClick={() => setActiveTab('perception')}
          className={`flex-1 py-1 text-center rounded-t border-b-2 transition ${
            activeTab === 'perception'
              ? 'border-emerald-400 text-emerald-400 bg-slate-900'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          VISION
        </button>
        <button
          onClick={() => setActiveTab('performance')}
          className={`flex-1 py-1 text-center rounded-t border-b-2 transition ${
            activeTab === 'performance'
              ? 'border-emerald-400 text-emerald-400 bg-slate-900'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          METRICS
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`flex-1 py-1 text-center rounded-t border-b-2 transition ${
            activeTab === 'audit'
              ? 'border-emerald-400 text-emerald-400 bg-slate-900'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          AUDIT
        </button>
      </div>

      {/* Tab Panels */}
      <div className="flex-1 overflow-y-auto pr-1 text-xs">
        {/* AGENT TAB */}
        {activeTab === 'agent' && (
          <div className="space-y-3">
            {lastResponse ? (
              <>
                <div className="bg-slate-900/80 p-3 rounded border border-slate-800">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300 mb-1">
                    <span>IMMUTABLE INTENT ANCHOR</span>
                    <span className="font-mono text-[9px] text-emerald-400">{lastResponse.intentAnchor?.immutableHash}</span>
                  </div>
                  <div className="space-y-1 font-mono text-[10px] text-slate-400">
                    <p><span className="text-slate-500">Goal:</span> {lastResponse.intentAnchor?.targetGoal}</p>
                    <p><span className="text-slate-500">Origin:</span> {lastResponse.intentAnchor?.originDomain}</p>
                  </div>
                </div>

                <div
                  className={`p-3 rounded border ${
                    lastResponse.firewallResult?.decision === 'ALLOW'
                      ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
                      : lastResponse.firewallResult?.decision === 'CONFIRM'
                      ? 'bg-amber-950/30 border-amber-500/30 text-amber-300'
                      : 'bg-rose-950/30 border-rose-500/30 text-rose-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1 font-bold">
                    <span className="flex items-center gap-1">
                      {lastResponse.firewallResult?.decision === 'ALLOW' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                      {lastResponse.firewallResult?.decision === 'CONFIRM' && <AlertTriangle className="w-4 h-4 text-amber-400" />}
                      {lastResponse.firewallResult?.decision === 'BLOCK' && <XCircle className="w-4 h-4 text-rose-400" />}
                      FIREWALL DECISION: {lastResponse.firewallResult?.decision}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 font-mono">
                      RISK: {lastResponse.firewallResult?.riskLevel}
                    </span>
                  </div>
                  <p className="text-[11px] mt-1">{lastResponse.firewallResult?.reason}</p>

                  {lastResponse.firewallResult?.decision === 'CONFIRM' && (
                    <button
                      onClick={handleConfirmAction}
                      className="mt-2 w-full py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded transition"
                    >
                      CONFIRM & EXECUTE HIGH-RISK ACTION
                    </button>
                  )}
                </div>

                <div className="bg-slate-900 p-3 rounded border border-slate-800 font-mono">
                  <h4 className="text-[11px] font-bold text-slate-300 mb-1">PROPOSED STRUCTURED ACTION</h4>
                  <pre className="text-[10px] text-slate-300 whitespace-pre-wrap bg-slate-950 p-2 rounded border border-slate-800">
                    {JSON.stringify(lastResponse.candidateAction, null, 2)}
                  </pre>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-slate-500 italic">
                No active agent task running. Enter a task above and click Run Agent.
              </div>
            )}
          </div>
        )}

        {/* PRIVACY TAB */}
        {activeTab === 'privacy' && (
          <div className="space-y-3">
            {lastResponse?.boundaryReport ? (
              <>
                <div className="bg-slate-900 p-3 rounded border border-slate-800">
                  <h4 className="font-bold text-xs text-emerald-400 mb-2 flex items-center justify-between">
                    <span>NETWORK PRIVACY ATTESTATION</span>
                    {lastResponse.boundaryReport.zeroRawPIIVerified && (
                      <span className="text-[9px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded">
                        ZERO RAW PII VERIFIED
                      </span>
                    )}
                  </h4>
                  <div className="grid grid-cols-2 gap-2 font-mono text-[10px]">
                    <div className="bg-slate-950 p-2 rounded">
                      <p className="text-slate-400">Entities Detected</p>
                      <p className="font-bold text-slate-100">{lastResponse.boundaryReport.rawEntitiesDetected}</p>
                    </div>
                    <div className="bg-slate-950 p-2 rounded">
                      <p className="text-slate-400">Entities Tokenized</p>
                      <p className="font-bold text-emerald-400">{lastResponse.boundaryReport.entitiesTokenized}</p>
                    </div>
                    <div className="bg-slate-950 p-2 rounded">
                      <p className="text-slate-400">Entities Blocked</p>
                      <p className="font-bold text-rose-400">{lastResponse.boundaryReport.entitiesBlocked}</p>
                    </div>
                    <div className="bg-slate-950 p-2 rounded">
                      <p className="text-slate-400">Payload Size</p>
                      <p className="font-bold text-slate-100">{lastResponse.boundaryReport.sanitizedPayloadSizeBytes} B</p>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900 p-3 rounded border border-slate-800">
                  <h4 className="font-bold text-[11px] text-slate-300 mb-1">INDEPENDENT EGRESS LOGS</h4>
                  <ul className="space-y-1 font-mono text-[10px] text-slate-400 max-h-40 overflow-y-auto">
                    {lastResponse.boundaryReport.validationDetails.map((log: string, idx: number) => (
                      <li key={idx} className="border-b border-slate-800/50 pb-0.5">{log}</li>
                    ))}
                  </ul>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-slate-500 italic">No privacy reports generated yet.</div>
            )}
          </div>
        )}

        {/* VISION TAB (PERCEPTION) */}
        {activeTab === 'perception' && (
          <div className="space-y-3 font-mono">
            {lastResponse?.mlBackendStatus ? (
              <>
                <div className="bg-slate-900 p-3 rounded border border-slate-800 space-y-1.5 text-[10px]">
                  <h4 className="font-bold text-xs text-slate-200 flex items-center gap-1">
                    <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                    LOCAL ML INFERENCE BACKEND
                  </h4>
                  <div className="flex justify-between bg-slate-950 p-1.5 rounded border border-slate-800">
                    <span className="text-slate-400">Active Backend:</span>
                    <span className="font-bold uppercase text-emerald-400">{lastResponse.mlBackendStatus.backend}</span>
                  </div>
                  <div className="flex justify-between bg-slate-950 p-1.5 rounded border border-slate-800">
                    <span className="text-slate-400">Model Name:</span>
                    <span className="text-slate-200">{lastResponse.mlBackendStatus.modelName}</span>
                  </div>
                  <div className="flex justify-between bg-slate-950 p-1.5 rounded border border-slate-800">
                    <span className="text-slate-400">Inference Latency:</span>
                    <span className="text-slate-200">{lastResponse.mlBackendStatus.inferenceLatencyMs}ms</span>
                  </div>
                </div>

                {lastResponse.boundaryReport?.visualRedactionVerified && (
                  <div className="bg-slate-900 p-3 rounded border border-slate-800 space-y-2 text-[10px]">
                    <h4 className="font-bold text-xs text-slate-200 flex items-center gap-1">
                      <ImageIcon className="w-3.5 h-3.5 text-emerald-400" />
                      CLIENT VISUAL REDACTION ARTIFACT
                    </h4>
                    <p className="text-slate-400">
                      Viewport screenshot obfuscated locally on HTML5 Canvas prior to network egress.
                    </p>
                    <div className="p-1 bg-slate-950 rounded border border-emerald-500/30 flex justify-center">
                      <span className="text-emerald-400 text-[10px] font-bold">✓ SANITIZED SCREENSHOT BASE64 GENERATED</span>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-slate-500 italic">No visual inference run yet.</div>
            )}
          </div>
        )}

        {/* METRICS TAB */}
        {activeTab === 'performance' && (
          <div className="space-y-3 font-mono">
            {ledgerData?.metrics ? (
              <div className="bg-slate-900 p-3 rounded border border-slate-800 space-y-2">
                <h4 className="font-bold text-xs text-slate-200">RECLASSIFIED PERFORMANCE & PRIVACY METRICS</h4>

                <div className="bg-slate-950 p-2 rounded border border-slate-800 space-y-1 text-[10px]">
                  <div className="flex justify-between">
                    <span className="text-slate-400">DOM Context Extraction Accuracy:</span>
                    <span className="font-bold text-slate-200">{ledgerData.metrics.domContextExtractionAccuracyPct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Visual Perception Accuracy:</span>
                    <span className="font-bold text-emerald-400">{ledgerData.metrics.visualPerceptionAccuracyPct}%</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div className="bg-slate-950 p-2 rounded border border-slate-800">
                    <p className="text-slate-400">Minimum Disclosure</p>
                    <p className="text-base font-bold text-emerald-400">
                      {ledgerData.metrics.minimumDisclosureScore}
                    </p>
                  </div>
                  <div className="bg-slate-950 p-2 rounded border border-slate-800">
                    <p className="text-slate-400">Privacy-Utility</p>
                    <p className="text-base font-bold text-emerald-400">
                      {ledgerData.metrics.privacyUtilityEfficiency}
                    </p>
                  </div>
                </div>

                <div className="bg-slate-950 p-2 rounded border border-slate-800 space-y-1 text-[10px]">
                  <p className="text-slate-400 font-bold border-b border-slate-800 pb-1">LATENCY BREAKDOWN (MS)</p>
                  <p className="flex justify-between"><span>Perception Latency:</span> <span>{ledgerData.metrics.perceptionLatencyMs}ms</span></p>
                  <p className="flex justify-between"><span>OCR Latency:</span> <span>{ledgerData.metrics.ocrLatencyMs}ms</span></p>
                  <p className="flex justify-between"><span>MDE Latency:</span> <span>{ledgerData.metrics.mdeLatencyMs}ms</span></p>
                  <p className="flex justify-between"><span>Firewall Latency:</span> <span>{ledgerData.metrics.firewallLatencyMs}ms</span></p>
                  <p className="flex justify-between font-bold text-emerald-400 pt-1 border-t border-slate-800">
                    <span>Total E2E Latency:</span> <span>{ledgerData.metrics.totalE2ELatencyMs}ms</span>
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 italic">No empirical metrics recorded yet.</div>
            )}
          </div>
        )}

        {/* AUDIT TAB */}
        {activeTab === 'audit' && (
          <div className="space-y-3 font-mono text-[10px]">
            {ledgerData?.privacyEntries ? (
              <div className="bg-slate-900 p-3 rounded border border-slate-800">
                <h4 className="font-bold text-xs text-slate-200 mb-2">PRIVACY LEDGER ENTRIES</h4>
                <div className="space-y-2">
                  {ledgerData.privacyEntries.map((ent, i) => (
                    <div key={i} className="bg-slate-950 p-2 rounded border border-slate-800">
                      <div className="flex justify-between font-bold text-emerald-400">
                        <span>{ent.entityType} {ent.isVisualOnly ? '[VISUAL-ONLY]' : ''}</span>
                        <span>{ent.treatment}</span>
                      </div>
                      <p className="text-slate-400">Display: {ent.maskedDisplay}</p>
                      <p className="text-slate-500">Crossed Network: {ent.crossedNetwork ? 'YES' : 'NO (BLOCKED/TOKENIZED)'}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 italic">No audit records logged yet.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
