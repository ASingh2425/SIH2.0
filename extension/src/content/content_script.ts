import { DOMExtractor } from './dom_extractor';
import { LocalPIIDetector } from '../privacy/pii_detector';
import { TaskIntentParser } from '../privacy/task_intent';
import { MinimumDisclosureEngine } from '../privacy/minimum_disclosure';
import { LocalActionFirewall } from '../firewall/action_firewall';
import { BrowserExecutor } from './action_executor';
import { ClientCanvasRedactor } from './canvas_capture';
import { validateNetworkEgress } from '../privacy/egress_validator';
import { PrivacyLedger } from '../ledger/privacy_ledger';
import { SanitizedContextPayload } from '../types/context';
import { DetectedEntity } from '../types/privacy';
import { IntentAnchor, StructuredAction } from '../types/action';

class ContentAgentController {
  private domExtractor = new DOMExtractor();
  private piiDetector = new LocalPIIDetector();
  private taskIntentParser = new TaskIntentParser();
  private mde = new MinimumDisclosureEngine();
  private firewall = new LocalActionFirewall();
  private executor = new BrowserExecutor();
  private redactor = new ClientCanvasRedactor();
  private ledger = PrivacyLedger.getInstance();

  private activeIntentAnchor: IntentAnchor | null = null;
  private currentLiveNodeMap = new Map<string, HTMLElement>();
  private outstandingCaptureNonces = new Map<string, { taskId: string; createdAt: number; origin: string }>();

  constructor() {
    this.initMessageListeners();
    console.log('[PrivacyGuard Content Agent] Active and listening in DOM.');
  }

  private generateCaptureNonce(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
      const buf = new Uint8Array(16);
      crypto.getRandomValues(buf);
      return Array.from(buf).map(b => b.toString(16).padStart(2, '0')).join('');
    }
    return 'nonce_' + Math.random().toString(36).substring(2) + '_' + Date.now();
  }

  private initMessageListeners() {
    chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
      if (request.type === 'START_TASK') {
        this.handleStartTask(request.userPrompt, request.taskId, request.forceSlowPath)
          .then(res => sendResponse(res))
          .catch(err => sendResponse({ error: err.message }));
        return true;
      }

      if (request.type === 'EXECUTE_CONFIRMED_ACTION') {
        this.handleConfirmedAction(request.action, request.firewallResult)
          .then(res => sendResponse(res))
          .catch(err => sendResponse({ error: err.message }));
        return true;
      }

      if (request.type === 'GET_LEDGER_DATA') {
        sendResponse(this.ledger.getFullLedger(request.taskId));
        return true;
      }
    });
  }

  private async handleStartTask(userPrompt: string, taskId: string, forceSlowPath = false) {
    const originDomain = window.location.origin;

    // 1. Create Immutable Local Intent Anchor
    this.activeIntentAnchor = this.taskIntentParser.createIntentAnchor(taskId, userPrompt, originDomain);

    // 2. Local Perception: Extract DOM tree
    const perceptionStart = performance.now();
    const { nodes, nodeMap } = this.domExtractor.extractDOMContext();
    this.currentLiveNodeMap = nodeMap;

    // Determine Tiered Path Execution (Fast Path vs Slow Path)
    const hasVisualElements = document.querySelector('canvas, svg, img') !== null;
    const isSlowPath = forceSlowPath || hasVisualElements;

    let rawEntities: DetectedEntity[] = [];
    let ocrLatencyMs = 0;
    let visualPrivacyState: 'VERIFIED_SAFE' | 'PII_DETECTED' | 'VISUAL_PRIVACY_UNVERIFIED' = 'VERIFIED_SAFE';
    let unverifiedVisualRegionsMasked = 0;
    let evaluatedEntities: DetectedEntity[] = [];
    let sanitizedScreenshotBase64: string | undefined = undefined;
    let imageAttestation: any = undefined;
    let currentCaptureNonce: string | undefined = undefined;

    if (isSlowPath) {
      // 3A. STEP 1: Capture Viewport Screenshot FIRST
      const captureNonce = this.generateCaptureNonce();
      currentCaptureNonce = captureNonce;
      this.outstandingCaptureNonces.set(captureNonce, { taskId, createdAt: Date.now(), origin: originDomain });

      const captureRes = await new Promise<{
        success: boolean;
        dataUrl?: string;
        taskId?: string;
        captureNonce?: string;
        tabId?: number;
        origin?: string;
        captureTimestamp?: number;
        visualPrivacyState?: 'VERIFIED_SAFE' | 'PII_DETECTED' | 'VISUAL_PRIVACY_UNVERIFIED';
        error?: string;
      }>(resolve => {
        if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
          chrome.runtime.sendMessage(
            {
              type: 'CAPTURE_VISIBLE_TAB',
              taskId,
              captureNonce,
              expectedOrigin: originDomain,
              viewportWidth: window.innerWidth,
              viewportHeight: window.innerHeight,
              devicePixelRatio: window.devicePixelRatio || 1,
            },
            res => {
              if (chrome.runtime.lastError) {
                resolve({ success: false, error: chrome.runtime.lastError.message });
              } else {
                resolve(res || { success: false, error: 'No response from capture service worker' });
              }
            }
          );
        } else {
          resolve({ success: false, error: 'Extension runtime unavailable' });
        }
      });

      // Single-use Nonce Consumption & Validation
      const nonceMeta = captureRes.captureNonce ? this.outstandingCaptureNonces.get(captureRes.captureNonce) : undefined;
      const isNonceValid = !!nonceMeta && nonceMeta.taskId === taskId && nonceMeta.origin === originDomain;
      if (captureRes.captureNonce) {
        this.outstandingCaptureNonces.delete(captureRes.captureNonce);
      }

      const now = Date.now();
      const isFresh = typeof captureRes.captureTimestamp === 'number' && (now - captureRes.captureTimestamp) <= 5000 && (now - captureRes.captureTimestamp) >= 0;
      const isActiveTask = this.activeIntentAnchor !== null && this.activeIntentAnchor.taskId === taskId;
      const isOriginMatch = captureRes.origin ? captureRes.origin === originDomain : true;
      const isTaskMatch = captureRes.taskId ? captureRes.taskId === taskId : true;

      const isCaptureValid = captureRes.success && captureRes.dataUrl && isNonceValid && isFresh && isActiveTask && isOriginMatch && isTaskMatch;

      if (isCaptureValid) {
        let rawDataUrl: string | undefined = captureRes.dataUrl;
        delete (captureRes as any).dataUrl; // Immediate memory cleanup

        try {
          // 3B. STEP 2: Execute Local Visual OCR & Multimodal Perception on Real Captured Screenshot Pixels
          const perceptionRes = await this.piiDetector.detectMultimodalEntities(nodes, document, rawDataUrl);
          rawEntities = perceptionRes.entities;
          ocrLatencyMs = perceptionRes.ocrLatencyMs;
          visualPrivacyState = perceptionRes.visualPrivacyState;
          unverifiedVisualRegionsMasked = perceptionRes.unverifiedVisualRegionsMasked;

          // 3C. STEP 3: Evaluate Minimum Disclosure Engine (MDE) on Fused Entity Set
          evaluatedEntities = this.mde.evaluateDisclosure(rawEntities, this.activeIntentAnchor);

          // 3D. STEP 4: Perform Solid Dark Fill Canvas Redaction (#020617) over Screenshot Pixels
          const redactRes = await this.redactor.redactViewportScreenshot(
            evaluatedEntities,
            window.innerWidth,
            window.innerHeight,
            rawDataUrl,
            window.devicePixelRatio || 1,
            taskId,
            captureNonce,
            'percept_' + Date.now()
          );

          if (redactRes.visualPrivacyState === 'VISUAL_PRIVACY_UNVERIFIED') {
            visualPrivacyState = 'VISUAL_PRIVACY_UNVERIFIED';
            sanitizedScreenshotBase64 = undefined;
          } else {
            sanitizedScreenshotBase64 = redactRes.sanitizedBase64 || undefined;
            imageAttestation = redactRes.attestation;
          }
        } catch (_err) {
          visualPrivacyState = 'VISUAL_PRIVACY_UNVERIFIED';
          sanitizedScreenshotBase64 = undefined;
        } finally {
          rawDataUrl = undefined; // Immediate raw reference release
        }
      } else {
        if (captureRes && (captureRes as any).dataUrl) {
          delete (captureRes as any).dataUrl;
        }
        visualPrivacyState = 'VISUAL_PRIVACY_UNVERIFIED';
        sanitizedScreenshotBase64 = undefined;
      }
    } else {
      // 3E. Fast Path (DOM-only perception without screenshot)
      const perceptionRes = await this.piiDetector.detectMultimodalEntities(nodes, document);
      rawEntities = perceptionRes.entities;
      ocrLatencyMs = perceptionRes.ocrLatencyMs;
      visualPrivacyState = perceptionRes.visualPrivacyState;
      unverifiedVisualRegionsMasked = perceptionRes.unverifiedVisualRegionsMasked;
      evaluatedEntities = this.mde.evaluateDisclosure(rawEntities, this.activeIntentAnchor);
    }

    const perceptionMs = performance.now() - perceptionStart;

    // Record privacy decisions in local ledger
    this.ledger.recordPerceptionDecisions(taskId, evaluatedEntities);

    // 4. Construct Sanitized DOM Payload
    const sanitizedNodes = nodes.map(n => {
      const ent = evaluatedEntities.find(e => e.nodeId === n.nodeId);
      if (ent) {
        if (ent.treatment === 'TOKENIZE') {
          return { ...n, text: ent.assignedToken, sanitizedValue: ent.assignedToken, appliedTreatment: ent.treatment, assignedToken: ent.assignedToken };
        } else if (ent.treatment === 'MASK' || ent.treatment === 'REMOVE') {
          return { ...n, text: ent.maskedDisplay, sanitizedValue: ent.maskedDisplay, appliedTreatment: ent.treatment };
        }
      }
      return n;
    });

    // 5. Independent Network Egress Validation & Boundary Attestation Generation
    const boundaryReport = validateNetworkEgress(
      evaluatedEntities,
      sanitizedNodes,
      sanitizedScreenshotBase64,
      visualPrivacyState,
      unverifiedVisualRegionsMasked,
      imageAttestation,
      taskId,
      currentCaptureNonce
    );
    this.ledger.recordBoundaryReport(boundaryReport);

    const mlBackendStatus = this.piiDetector.getVisualDetector().getBackendStatus();

    const sanitizedPayload: SanitizedContextPayload = {
      taskId,
      timestamp: Date.now(),
      originDomain,
      viewport: { width: window.innerWidth, height: window.innerHeight },
      sanitizedDomNodes: sanitizedNodes,
      sanitizedScreenshotBase64,
      mlBackendStatus,
      boundaryReport,
    };

    // 6. Send Sanitized Payload to Remote Reasoning Server
    const reasonerResponse = await this.queryRemoteReasoningServer(sanitizedPayload);
    const candidateAction = reasonerResponse.candidateAction;

    // 7. Local Action Firewall Authorization
    const structuredAction: StructuredAction = {
      actionId: candidateAction.actionId || `act_${Date.now()}`,
      taskId,
      action: candidateAction.actionType as any,
      target: { nodeId: candidateAction.targetNodeId || 'N/A' },
      value: candidateAction.value,
      confidence: 0.95,
      reasoning: candidateAction.expectedResult || 'Execute user task action',
    };
    const firewallResult = this.firewall.validateAction(
      structuredAction,
      this.activeIntentAnchor!,
      originDomain,
      this.currentLiveNodeMap
    );
    this.ledger.recordFirewallDecision(taskId, structuredAction, firewallResult);

    return {
      taskId,
      intentAnchor: this.activeIntentAnchor,
      firewallResult,
      candidateAction,
      boundaryReport,
      mlBackendStatus,
      timing: {
        perceptionMs: Math.round(perceptionMs),
        ocrLatencyMs: Math.round(ocrLatencyMs),
      },
    };
  }

  private async queryRemoteReasoningServer(payload: SanitizedContextPayload): Promise<any> {
    const isMock = true; // Simulated local mock remote reasoner server
    if (isMock) {
      await new Promise(r => setTimeout(r, 200));

      const userGoal = this.activeIntentAnchor?.targetGoal || '';
      let actionType = 'CLICK';
      let targetNodeId = 'btn_search';
      let value = undefined;

      if (userGoal.toLowerCase().includes('delhi')) {
        actionType = 'TYPE';
        targetNodeId = 'input_destination';
        value = 'Delhi';
      }

      return {
        status: 'SUCCESS',
        candidateAction: {
          actionId: `act_${Date.now()}`,
          actionType,
          targetNodeId,
          value,
          expectedResult: 'Proceed to flight search results',
        },
      };
    }

    const response = await fetch('https://api.reasoner.local/agent/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return await response.json();
  }

  private async handleConfirmedAction(action: any, firewallResult: any) {
    if (!this.activeIntentAnchor) {
      throw new Error('No active intent anchor bound to session');
    }

    const structuredAction: StructuredAction = {
      actionId: action.actionId || `act_${Date.now()}`,
      taskId: this.activeIntentAnchor.taskId,
      action: action.actionType as any,
      target: { nodeId: action.targetNodeId || 'N/A' },
      value: action.value,
      confidence: 0.95,
      reasoning: action.expectedResult || 'Confirmed action execution',
    };

    return await this.executor.executeVerifiedAction(
      structuredAction,
      this.currentLiveNodeMap,
      window.location.origin,
      firewallResult.authorizationToken,
      this.firewall
    );
  }
}

new ContentAgentController();
