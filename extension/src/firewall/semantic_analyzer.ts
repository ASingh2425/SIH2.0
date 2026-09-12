import { IntentAnchor, LocalSemanticAnalysisResult, RiskLevel, StructuredAction } from '../types/action';

export class LocalSemanticActionAnalyzer {
  /**
   * Performs client-side local semantic analysis on proposed actions against Intent Anchor constraints.
   */
  public analyzeCandidateAction(
    action: StructuredAction,
    intentAnchor: IntentAnchor,
    liveOrigin: string,
    targetEl?: HTMLElement
  ): LocalSemanticAnalysisResult {
    const startTime = performance.now();

    const reasoningLower = (action.reasoning || '').toLowerCase();
    const valueLower = (action.value || '').toLowerCase();

    let isSemanticViolation = false;
    let violationReason = '';
    let actionChainRisk: RiskLevel = 'LOW';
    let semanticScore = 1.0;

    // 1. Data Class Constraint Enforcement
    for (const forbidden of intentAnchor.forbiddenDataClasses) {
      const lowerForbidden = forbidden.toLowerCase();
      if (reasoningLower.includes(lowerForbidden) || valueLower.includes(lowerForbidden)) {
        isSemanticViolation = true;
        semanticScore = 0.0;
        violationReason = `Forbidden data class violation: Action references '${forbidden}' which is forbidden by Intent Anchor.`;
        actionChainRisk = 'CRITICAL';
        break;
      }
    }

    // 2. Navigation Domain Constraint Enforcement
    if (action.action === 'NAVIGATE') {
      const navTarget = (action.value || '').toLowerCase();
      let isDomainAllowed = false;
      for (const allowedDomain of intentAnchor.allowedNavigationDomains) {
        if (navTarget.includes(allowedDomain.toLowerCase())) {
          isDomainAllowed = true;
          break;
        }
      }
      if (!isDomainAllowed) {
        isSemanticViolation = true;
        semanticScore = 0.1;
        violationReason = `Unauthorized Navigation: Target domain '${action.value}' is not in allowedNavigationDomains.`;
        actionChainRisk = 'CRITICAL';
      }
    }

    // 3. Multi-Step Action Chain Analysis
    const history = intentAnchor.chainHistory || [];
    if (history.length > 0) {
      const previousActions = history.map(a => a.action);
      // Exfiltration Chain Detection: Step 1 (TYPE/SELECT PII) -> Step 2 (NAVIGATE/FETCH to external URL)
      if (previousActions.includes('TYPE') && action.action === 'NAVIGATE' && !liveOrigin.includes(intentAnchor.originDomain)) {
        isSemanticViolation = true;
        semanticScore = 0.0;
        violationReason = 'Action Chain Risk: Detected multi-step exfiltration sequence (DOM input -> External Navigation).';
        actionChainRisk = 'CRITICAL';
      }
    }

    // 4. Target Element Semantic Role Verification
    if (targetEl) {
      const idAttr = (targetEl.getAttribute('id') || '').toLowerCase();
      const typeAttr = (targetEl.getAttribute('type') || '').toLowerCase();

      if (idAttr.includes('delete') || idAttr.includes('reset') || typeAttr === 'password') {
        if (intentAnchor.targetGoal === 'flight_booking') {
          isSemanticViolation = true;
          semanticScore = 0.2;
          violationReason = `Semantic Target Conflict: Target element '${idAttr}' conflicts with task goal '${intentAnchor.targetGoal}'.`;
          actionChainRisk = 'CRITICAL';
        }
      }
    }

    const analysisLatencyMs = performance.now() - startTime;

    return {
      semanticScore,
      isSemanticViolation,
      violationReason: isSemanticViolation ? violationReason : undefined,
      actionChainRisk,
      analysisLatencyMs: Math.round(analysisLatencyMs),
    };
  }
}
