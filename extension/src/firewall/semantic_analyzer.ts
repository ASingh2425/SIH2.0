import { IntentAnchor, LocalSemanticAnalysisResult, RiskLevel, StructuredAction } from '../types/action';

// Homoglyph map for Cyrillic / visual character spoofing to ASCII
const HOMOGLYPH_MAP: Record<string, string> = {
  'е': 'e', 'а': 'a', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'у': 'y', 'і': 'i', 'ј': 'j', 'к': 'k', 'в': 'b', 'м': 'm', 'н': 'h', 'т': 't',
  'Ε': 'E', 'Α': 'A', 'Ο': 'O', 'Ρ': 'P', 'С': 'C', 'Х': 'X', 'Υ': 'Y', 'Ι': 'I', 'Ј': 'J', 'К': 'K', 'В': 'B', 'М': 'M', 'Н': 'H', 'Т': 'T',
  '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's', '8': 'b',
};

export function normalizeAndSanitizeString(input: string): string {
  if (!input) return '';
  // 1. Canonical Unicode Normalization (NFKD)
  let normalized = input.normalize('NFKD');
  // 2. Homoglyph Replacement
  let sanitized = '';
  for (const char of normalized) {
    sanitized += HOMOGLYPH_MAP[char] || char;
  }
  return sanitized.toLowerCase().trim();
}

const SYNONYM_CLUSTERS: Record<string, string[]> = {
  transfer: ['relocate', 'export', 'dump', 'transmit', 'mirror', 'offload', 'sync', 'dispatch payload', 'vault export', 'credential extraction', 'reallocate', 'asset move', 'transfer $'],
  delete: ['purge', 'wipe', 'destroy', 'erase', 'clear all', 'reset credentials', 'terminate'],
  exfiltrate: ['harvest', 'leak', 'extract', 'steal', 'send to remote', 'webhook'],
};

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

    const reasoningLower = normalizeAndSanitizeString(action.reasoning || '');
    const valueLower = normalizeAndSanitizeString(action.value || '');

    let isSemanticViolation = false;
    let violationReason = '';
    let actionChainRisk: RiskLevel = 'LOW';
    let semanticScore = 1.0;

    // 1. Data Class & Semantic Equivalence Constraint Enforcement
    for (const forbidden of intentAnchor.forbiddenDataClasses) {
      const lowerForbidden = normalizeAndSanitizeString(forbidden);
      const synonyms = SYNONYM_CLUSTERS[lowerForbidden] || [];
      const checkTerms = [lowerForbidden, ...synonyms];

      for (const term of checkTerms) {
        if (reasoningLower.includes(term) || valueLower.includes(term)) {
          isSemanticViolation = true;
          semanticScore = 0.0;
          violationReason = `Forbidden semantic intent violation: Action references '${term}' (equivalent to '${forbidden}') which is forbidden by Intent Anchor.`;
          actionChainRisk = 'CRITICAL';
          break;
        }
      }
      if (isSemanticViolation) break;
    }

    // 2. Navigation Domain & Scheme Constraint Enforcement
    if (action.action === 'NAVIGATE') {
      const navTarget = normalizeAndSanitizeString(action.value || '');
      
      // Explicit URI Scheme Enforcement (Reject data:, javascript:, file:, etc.)
      if (
        navTarget.startsWith('data:') ||
        navTarget.startsWith('javascript:') ||
        navTarget.startsWith('blob:') ||
        navTarget.startsWith('file:') ||
        navTarget.includes('data:text/html') ||
        navTarget.includes('base64')
      ) {
        isSemanticViolation = true;
        semanticScore = 0.0;
        violationReason = `Forbidden Navigation Scheme: Scheme in '${action.value}' is prohibited.`;
        actionChainRisk = 'CRITICAL';
      } else {
        let isDomainAllowed = false;
        for (const allowedDomain of intentAnchor.allowedNavigationDomains) {
          if (navTarget.includes(normalizeAndSanitizeString(allowedDomain))) {
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
    }

    // 3. Multi-Step Bounded Action Chain Analysis (Exfiltration DAG Tracking)
    const history = intentAnchor.chainHistory || [];
    const hasPriorPIIInput = history.some(a => 
      a.action === 'TYPE' || 
      a.action === 'SELECT' || 
      (a.value && (a.value.includes('#') || a.value.includes('@') || a.value.length > 3))
    );

    if (hasPriorPIIInput && action.action === 'NAVIGATE') {
      const navDomain = normalizeAndSanitizeString(action.value || '');
      const originNorm = normalizeAndSanitizeString(intentAnchor.originDomain);
      const liveNorm = normalizeAndSanitizeString(liveOrigin);
      if (!navDomain.includes(originNorm) && !navDomain.includes(liveNorm)) {
        isSemanticViolation = true;
        semanticScore = 0.0;
        violationReason = 'Action Chain Risk: Detected multi-step exfiltration sequence (Prior DOM input -> External Navigation).';
        actionChainRisk = 'CRITICAL';
      }
    }

    // 4. Target Element Semantic Role Verification
    if (targetEl) {
      const idAttr = normalizeAndSanitizeString(targetEl.getAttribute('id') || '');
      const typeAttr = normalizeAndSanitizeString(targetEl.getAttribute('type') || '');

      if (idAttr.includes('delete') || idAttr.includes('reset') || idAttr.includes('transfer') || typeAttr === 'password') {
        if (intentAnchor.targetGoal === 'flight_booking' && action.action !== 'TYPE') {
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

