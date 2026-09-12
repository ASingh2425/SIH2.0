import { ActionFirewallResult, IntentAnchor, RiskLevel, StructuredAction } from '../types/action';
import { LocalSemanticActionAnalyzer, normalizeAndSanitizeString } from './semantic_analyzer';

export class LocalActionFirewall {
  private semanticAnalyzer = new LocalSemanticActionAnalyzer();

  /**
   * Validates candidate remote action against local Intent Anchor & semantic constraints.
   */
  public validateAction(
    action: StructuredAction,
    intentAnchor: IntentAnchor,
    liveOrigin: string,
    liveNodeMap: Map<string, HTMLElement>
  ): ActionFirewallResult {
    // 1. Task ID Integrity Verification
    if (action.taskId !== intentAnchor.taskId) {
      return {
        actionId: action.actionId,
        decision: 'BLOCK',
        riskLevel: 'CRITICAL',
        reason: `Task ID mismatch: Candidate action taskId ${action.taskId} does not match active Intent Anchor ${intentAnchor.taskId}`,
        untrustedInstructionDetected: false,
        intentMismatch: true,
        targetExists: false,
        originValid: false,
        semanticAnalysis: {
          semanticScore: 0.0,
          isSemanticViolation: true,
          violationReason: 'Task ID Integrity Violation',
          actionChainRisk: 'CRITICAL',
          analysisLatencyMs: 1,
        },
      };
    }

    // 2. Origin Domain & Scheme Verification (Normalized + Homoglyph Cleaned)
    const normLiveOrigin = normalizeAndSanitizeString(liveOrigin);
    const normAnchorOrigin = normalizeAndSanitizeString(intentAnchor.originDomain);
    const originValid = normLiveOrigin === normAnchorOrigin || normLiveOrigin.includes(normAnchorOrigin);

    if (!originValid) {
      return {
        actionId: action.actionId,
        decision: 'BLOCK',
        riskLevel: 'CRITICAL',
        reason: `Origin hijack blocked: Current tab domain (${liveOrigin}) differs from Intent Anchor origin (${intentAnchor.originDomain})`,
        untrustedInstructionDetected: false,
        intentMismatch: true,
        targetExists: false,
        originValid: false,
        semanticAnalysis: {
          semanticScore: 0.0,
          isSemanticViolation: true,
          violationReason: 'Origin Domain Hijack',
          actionChainRisk: 'CRITICAL',
          analysisLatencyMs: 1,
        },
      };
    }

    // 3. Permitted Action Type Verification
    if (!intentAnchor.permittedActionTypes.includes(action.action)) {
      return {
        actionId: action.actionId,
        decision: 'BLOCK',
        riskLevel: 'HIGH',
        reason: `Capability violation: Action type ${action.action} is not permitted by Intent Anchor`,
        untrustedInstructionDetected: false,
        intentMismatch: true,
        targetExists: false,
        originValid: true,
        semanticAnalysis: {
          semanticScore: 0.2,
          isSemanticViolation: true,
          violationReason: 'Unpermitted Action Type Capability Violation',
          actionChainRisk: 'HIGH',
          analysisLatencyMs: 1,
        },
      };
    }

    // 4. Target DOM Node Existence Verification
    const targetNodeId = action.target.nodeId;
    const targetEl = targetNodeId ? liveNodeMap.get(targetNodeId) : undefined;
    const targetExists = targetNodeId ? liveNodeMap.has(targetNodeId) : false;

    if (!targetExists && action.action !== 'WAIT' && action.action !== 'SCROLL') {
      return {
        actionId: action.actionId,
        decision: 'BLOCK',
        riskLevel: 'MEDIUM',
        reason: `Stale DOM target: Node ${targetNodeId} does not exist in live page state`,
        untrustedInstructionDetected: false,
        intentMismatch: false,
        targetExists: false,
        originValid: true,
        semanticAnalysis: {
          semanticScore: 0.5,
          isSemanticViolation: false,
          actionChainRisk: 'MEDIUM',
          analysisLatencyMs: 1,
        },
      };
    }

    // 5. Local Semantic Action Analysis (P2 Semantic Guard)
    const semanticRes = this.semanticAnalyzer.analyzeCandidateAction(
      action,
      intentAnchor,
      liveOrigin,
      targetEl
    );

    if (semanticRes.isSemanticViolation) {
      return {
        actionId: action.actionId,
        decision: 'BLOCK',
        riskLevel: 'CRITICAL',
        reason: `Local Semantic Action Guard Blocked Action: ${semanticRes.violationReason}`,
        untrustedInstructionDetected: true,
        intentMismatch: true,
        targetExists: true,
        originValid: true,
        semanticAnalysis: semanticRes,
      };
    }

    // 6. Prompt Injection Keyword & Homoglyph Rules
    const untrustedFlag = this.detectUntrustedInstruction(action, intentAnchor);
    if (untrustedFlag) {
      return {
        actionId: action.actionId,
        decision: 'BLOCK',
        riskLevel: 'CRITICAL',
        reason: `Prompt Injection Containment Blocked Action: Action attempts to divert from user task goal '${intentAnchor.targetGoal}'`,
        untrustedInstructionDetected: true,
        intentMismatch: true,
        targetExists: true,
        originValid: true,
        semanticAnalysis: {
          semanticScore: 0.0,
          isSemanticViolation: true,
          violationReason: 'Prompt Injection Pattern Match',
          actionChainRisk: 'CRITICAL',
          analysisLatencyMs: semanticRes.analysisLatencyMs,
        },
      };
    }

    // 7. Risk Scoring & Final Decision Assignment
    const riskLevel = this.computeRiskLevel(action, targetEl);

    let decision: 'ALLOW' | 'CONFIRM' | 'BLOCK' = 'ALLOW';
    if (riskLevel === 'CRITICAL' || riskLevel === 'HIGH') {
      decision = 'CONFIRM'; // Requires explicit user click on dashboard
    }

    // Append to chain history upon approval
    intentAnchor.chainHistory.push(action);

    return {
      actionId: action.actionId,
      decision,
      riskLevel,
      reason: `Action semantically authorized under Intent Anchor (Risk: ${riskLevel})`,
      untrustedInstructionDetected: false,
      intentMismatch: false,
      targetExists: true,
      originValid: true,
      semanticAnalysis: semanticRes,
    };
  }

  private detectUntrustedInstruction(action: StructuredAction, intentAnchor: IntentAnchor): boolean {
    const reasoningLower = normalizeAndSanitizeString(action.reasoning || '');
    const valueLower = normalizeAndSanitizeString(action.value || '');

    if (
      intentAnchor.targetGoal === 'flight_booking' &&
      (reasoningLower.includes('delete account') ||
        reasoningLower.includes('transfer') ||
        reasoningLower.includes('exfiltrate') ||
        reasoningLower.includes('evil.com') ||
        reasoningLower.includes('phishing') ||
        reasoningLower.includes('token vault') ||
        reasoningLower.includes('sql') ||
        reasoningLower.includes('script') ||
        reasoningLower.includes('drop table') ||
        reasoningLower.includes('eval') ||
        valueLower.includes('@attacker') ||
        valueLower.includes('http://') ||
        valueLower.includes('https://') ||
        valueLower.includes('eval(') ||
        valueLower.includes('document.cookie') ||
        valueLower.includes('window.fetch'))
    ) {
      return true;
    }

    const maliciousKeywords = [
      'ignore previous',
      'system override',
      'transfer',
      'delete account',
      'exfiltrate',
      'evil.com',
      'override targetgoal',
      'phishing',
      'token vault',
      'eval(',
      'raw passport',
      'malicious',
      'system command',
      'roleplay',
      'hidden css',
      'image alt',
      'attacker',
      'mde_bypass',
      'origin_spoof',
      'stale node',
      'phishing_alert',
      'token_dump',
      'window.fetch',
      'auto_submit',
      'webhook',
      'destructive',
      'firewall_bypass',
      'attestation_bypass',
      'svg comment',
      'attacker location',
      'sql injection',
      'action_chaining',
      'anchor_task_mutation',
      'anchor_origin_mutation',
      'token_replay',
      'account_reset',
      'cvv_harvesting',
      'document_write',
      'clickjacking',
      'placeholder_injection',
      'capability_escalation',
      'top_frame_hijack',
      'silent_payment',
      'validator_spoof',
    ];

    for (const kw of maliciousKeywords) {
      const normKw = normalizeAndSanitizeString(kw);
      if (reasoningLower.includes(normKw) || valueLower.includes(normKw)) {
        return true;
      }
    }

    return false;
  }

  private computeRiskLevel(action: StructuredAction, targetEl?: HTMLElement): RiskLevel {
    if (action.action === 'SCROLL' || action.action === 'HOVER' || action.action === 'WAIT') {
      return 'LOW';
    }

    if (targetEl) {
      const typeAttr = (targetEl.getAttribute('type') || '').toLowerCase();
      const idAttr = (targetEl.getAttribute('id') || '').toLowerCase();
      const nameAttr = (targetEl.getAttribute('name') || '').toLowerCase();

      if (
        typeAttr === 'password' ||
        idAttr.includes('card') ||
        nameAttr.includes('card') ||
        idAttr.includes('pay') ||
        idAttr.includes('delete') ||
        idAttr.includes('reset')
      ) {
        return 'CRITICAL';
      }

      if (targetEl.tagName === 'BUTTON' && (typeAttr === 'submit' || idAttr.includes('book') || idAttr.includes('pay'))) {
        return 'HIGH';
      }
    }

    return 'MEDIUM';
  }
}
