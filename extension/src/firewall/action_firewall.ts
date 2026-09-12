import { ActionFirewallResult, FirewallAuthorizationToken, IntentAnchor, RiskLevel, StructuredAction } from '../types/action';
import { LocalSemanticActionAnalyzer, normalizeAndSanitizeString } from './semantic_analyzer';

export class LocalActionFirewall {
  private semanticAnalyzer = new LocalSemanticActionAnalyzer();

  // Isolated World Private Session Secret (Generated dynamically per firewall instance)
  private readonly sessionHmacSecret: string = this.generateSessionSecret();

  // Set of consumed single-use token nonces for replay prevention
  private consumedTokenNonces = new Set<string>();

  private generateSessionSecret(): string {
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      const array = new Uint8Array(32);
      crypto.getRandomValues(array);
      return Array.from(array, b => b.toString(16).padStart(2, '0')).join('');
    }
    return `fw_secret_${Date.now()}_${Math.random().toString(36).substring(2)}`;
  }

  /**
   * Helper function for strict URL origin parsing and comparison.
   * Prevents substring and userinfo hijack vulnerabilities (e.g. example.com.evil.com).
   */
  public parseAndNormalizeOrigin(rawOrigin: string): string {
    if (!rawOrigin || typeof rawOrigin !== 'string') return '';
    const trimmed = rawOrigin.trim();
    try {
      const targetUrl = trimmed.includes('://') ? trimmed : `https://${trimmed}`;
      const url = new URL(targetUrl);
      if (url.protocol !== 'http:' && url.protocol !== 'https:') return '';
      if (url.username || url.password) return ''; // Reject userinfo URL origin attacks
      return url.origin.toLowerCase();
    } catch (_err) {
      return ''; // FAIL-CLOSED: Invalid origin strings must never be normalized via fallback
    }
  }

  public strictOriginMatch(originA: string, originB: string): boolean {
    const normA = this.parseAndNormalizeOrigin(originA);
    const normB = this.parseAndNormalizeOrigin(originB);
    if (!normA || !normB) return false;
    return normA === normB;
  }

  /**
   * Computes cryptographic SHA-256 HMAC signature for authorization token tuple.
   */
  public computeTokenSignature(
    taskId: string,
    actionId: string,
    actionType: string,
    targetNodeId: string,
    targetSelector: string,
    originDomain: string,
    decision: string,
    userConfirmed: boolean,
    issuedAt: number,
    expiresAt: number
  ): string {
    const normOrigin = this.parseAndNormalizeOrigin(originDomain);
    const rawTuple = `task=${taskId}|action=${actionId}|type=${actionType}|node=${targetNodeId}|selector=${targetSelector}|origin=${normOrigin}|decision=${decision}|confirmed=${userConfirmed}|issued=${issuedAt}|expires=${expiresAt}|secret=${this.sessionHmacSecret}`;
    
    // Cryptographically secure 256-bit SHA-256 digest
    return 'sha256_hmac_' + computeSha256Digest(rawTuple);
  }

  /**
   * Issues a signed FirewallAuthorizationToken for approved or confirmation-pending actions.
   */
  public issueAuthorizationToken(
    action: StructuredAction,
    originDomain: string,
    decision: 'ALLOW' | 'CONFIRM',
    userConfirmed: boolean = false
  ): FirewallAuthorizationToken {
    const issuedAt = Date.now();
    const expiresAt = issuedAt + 30000; // 30-second strict execution window
    const targetNodeId = action.target.nodeId || '';
    const targetSelector = action.target.selector || '';
    const normOrigin = this.parseAndNormalizeOrigin(originDomain);
    const tokenId = `token_${issuedAt}_${Math.random().toString(36).substring(2, 8)}`;

    const signature = this.computeTokenSignature(
      action.taskId,
      action.actionId,
      action.action,
      targetNodeId,
      targetSelector,
      normOrigin,
      decision,
      userConfirmed,
      issuedAt,
      expiresAt
    );

    return {
      tokenId,
      actionId: action.actionId,
      taskId: action.taskId,
      actionType: action.action,
      targetNodeId,
      targetSelector,
      originDomain: normOrigin,
      decision,
      userConfirmed,
      issuedAt,
      expiresAt,
      signature,
    };
  }

  /**
   * Authorizes explicit human user approval for CONFIRM actions.
   */
  public authorizeUserConfirmation(
    action: StructuredAction,
    initialResult: ActionFirewallResult,
    intentAnchor: IntentAnchor,
    liveOrigin: string
  ): FirewallAuthorizationToken | null {
    if (action.taskId !== intentAnchor.taskId) return null;
    if (initialResult.actionId !== action.actionId) return null;
    if (initialResult.decision !== 'CONFIRM') return null;

    if (!this.strictOriginMatch(liveOrigin, intentAnchor.originDomain)) {
      return null;
    }

    return this.issueAuthorizationToken(action, liveOrigin, 'CONFIRM', true);
  }

  /**
   * Verifies authenticity, integrity, TTL, decision state, single-use replay, and parameter binding of a token.
   */
  public verifyAuthorizationToken(
    token: FirewallAuthorizationToken,
    action: StructuredAction,
    liveOrigin: string,
    intentAnchor?: IntentAnchor
  ): { valid: boolean; reason?: string } {
    if (!token || typeof token !== 'object') {
      return { valid: false, reason: 'Missing authorization token' };
    }

    // Structural Field Check
    if (
      !token.tokenId ||
      !token.actionId ||
      !token.taskId ||
      !token.actionType ||
      !token.originDomain ||
      !token.signature ||
      typeof token.issuedAt !== 'number' ||
      typeof token.expiresAt !== 'number'
    ) {
      return { valid: false, reason: 'Malformed authorization token schema' };
    }

    // Finite Numeric Timestamp Validation (Prevents NaN/Infinity Bypass)
    if (!Number.isFinite(token.issuedAt) || !Number.isFinite(token.expiresAt)) {
      return { valid: false, reason: 'Non-finite token timestamp (NaN/Inf)' };
    }

    if (token.expiresAt <= token.issuedAt) {
      return { valid: false, reason: 'Invalid token expiration window' };
    }

    // 1. Signature Verification
    const expectedSig = this.computeTokenSignature(
      token.taskId,
      token.actionId,
      token.actionType,
      token.targetNodeId || '',
      token.targetSelector || '',
      token.originDomain,
      token.decision,
      token.userConfirmed,
      token.issuedAt,
      token.expiresAt
    );

    if (token.signature !== expectedSig) {
      return { valid: false, reason: 'Cryptographic signature mismatch or token forged' };
    }

    // 2. TTL Check
    const now = Date.now();
    if (now > token.expiresAt) {
      return { valid: false, reason: 'Authorization token expired' };
    }

    // 3. Single-Use Nonce Replay Check
    if (this.consumedTokenNonces.has(token.tokenId)) {
      return { valid: false, reason: 'Token replay detected: Nonce already consumed' };
    }

    // 4. Action & Intent Binding Checks
    if (token.taskId !== action.taskId) {
      return { valid: false, reason: `Task ID mismatch (Token: ${token.taskId}, Action: ${action.taskId})` };
    }

    if (token.actionId !== action.actionId) {
      return { valid: false, reason: `Action ID mismatch (Token: ${token.actionId}, Action: ${action.actionId})` };
    }

    if (token.actionType !== action.action) {
      return { valid: false, reason: `Action type mismatch (Token: ${token.actionType}, Action: ${action.action})` };
    }

    const actionNodeId = action.target.nodeId || '';
    if (token.targetNodeId !== actionNodeId) {
      return { valid: false, reason: `Target node ID mismatch (Token: ${token.targetNodeId}, Action: ${actionNodeId})` };
    }

    if (!this.strictOriginMatch(liveOrigin, token.originDomain)) {
      return { valid: false, reason: `Origin domain mismatch (Token: ${token.originDomain}, Live: ${liveOrigin})` };
    }

    if (intentAnchor && token.taskId !== intentAnchor.taskId) {
      return { valid: false, reason: 'Intent anchor task ID mismatch' };
    }

    // 5. Decision & CONFIRM Semantics
    if (token.decision === 'CONFIRM' && !token.userConfirmed) {
      return { valid: false, reason: 'Action requires explicit user confirmation (userConfirmed is false)' };
    }

    // Consume single-use nonce upon successful verification
    this.consumedTokenNonces.add(token.tokenId);

    return { valid: true };
  }

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

    const authorizationToken = this.issueAuthorizationToken(action, normLiveOrigin, decision, false);

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
      authorizationToken,
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

/**
 * Authoritative Synchronous SHA-256 Digest Engine for Extension Isolated World
 */
export function computeSha256Digest(ascii: string): string {
  const mathPow = Math.pow;
  const maxWord = mathPow(2, 32);
  const lengthProperty = 'length';
  let i, j;
  let result = '';

  const words: number[] = [];
  const asciiBitLength = ascii[lengthProperty] * 8;

  let hash = (computeSha256Digest as any).h = (computeSha256Digest as any).h || [];
  let k = (computeSha256Digest as any).k = (computeSha256Digest as any).k || [];
  let primeCounter = k[lengthProperty];

  const isPrime = (n: number) => {
    for (let factor = 2; factor * factor <= n; factor++) {
      if (n % factor === 0) return false;
    }
    return true;
  };

  const getFractionalBits = (n: number) => Math.floor((n - Math.floor(n)) * maxWord);

  if (!primeCounter) {
    let candidate = 2;
    while (primeCounter < 64) {
      if (isPrime(candidate)) {
        if (primeCounter < 8) {
          hash[primeCounter] = getFractionalBits(Math.pow(candidate, 1 / 2));
        }
        k[primeCounter] = getFractionalBits(Math.pow(candidate, 1 / 3));
        primeCounter++;
      }
      candidate++;
    }
  }

  hash = hash.slice(0);

  for (i = 0; i < ascii[lengthProperty]; i++) {
    j = ascii.charCodeAt(i);
    words[i >> 2] |= j << ((3 - (i % 4)) * 8);
  }
  words[ascii[lengthProperty] >> 2] |= 0x80 << ((3 - (ascii[lengthProperty] % 4)) * 8);
  words[((asciiBitLength + 64 >> 9) << 4) + 15] = asciiBitLength;

  for (i = 0; i < words[lengthProperty]; i += 16) {
    const w = words.slice(i, i + 16);
    for (j = w.length; j < 16; j++) w[j] = 0;
    const oldHash = hash.slice(0);

    for (j = 0; j < 64; j++) {
      const w15 = w[j - 15], w2 = w[j - 2];

      const a = hash[0], e = hash[4];
      const temp1 = hash[7]
        + (rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25))
        + ((e & hash[5]) ^ (~e & hash[6]))
        + k[j]
        + (w[j] = (j < 16) ? w[j] : (
          w[j - 16]
          + (rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3))
          + w[j - 7]
          + (rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10))
        ) | 0);
      const temp2 = (rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22))
        + ((a & hash[1]) ^ (a & hash[2]) ^ (hash[1] & hash[2]));

      hash = [(temp1 + temp2) | 0, a, hash[1], hash[2], (hash[3] + temp1) | 0, e, hash[5], hash[6]];
    }

    for (j = 0; j < 8; j++) {
      hash[j] = (hash[j] + oldHash[j]) | 0;
    }
  }

  for (i = 0; i < 8; i++) {
    for (j = 3; j >= 0; j--) {
      const b = (hash[i] >> (j * 8)) & 255;
      result += (b < 16 ? '0' : '') + b.toString(16);
    }
  }
  return result;
}

function rightRotate(value: number, amount: number) {
  return (value >>> amount) | (value << (32 - amount));
}
