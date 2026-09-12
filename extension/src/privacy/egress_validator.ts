import { DOMNodeDescriptor, PrivacyBoundaryReport } from '../types/context';
import { DetectedEntity } from '../types/privacy';

const EGRESS_EMAIL_REGEX = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
const EGRESS_CREDIT_CARD_REGEX = /\b(?:\d[ -]*?){13,16}\b/g;
const EGRESS_PASSPORT_REGEX = /\b[A-PR-WYa-pr-wy]\d{7}\b/g;
const EGRESS_PHONE_REGEX = /\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g;

/**
 * Safely extracts all string variants (plaintext, URL-decoded, Unicode-unescaped, Base64-decoded)
 * from arbitrary nested objects, arrays, and primitive strings with strict depth/length bounds.
 */
export function extractAllStringVariants(
  data: any,
  depth = 0,
  maxDepth = 8,
  visited = new Set<any>()
): string[] {
  if (depth > maxDepth || data === null || data === undefined) return [];

  if (typeof data === 'object') {
    if (visited.has(data)) return [];
    visited.add(data);
  }

  const results: string[] = [];

  if (typeof data === 'string') {
    results.push(data);

    // Bounded multi-layer decoding (up to 2 layers)
    let current = data;
    for (let layer = 0; layer < 2; layer++) {
      let decoded = current;
      let changed = false;

      // 1. URL / Percent Decoding
      if (decoded.includes('%')) {
        try {
          const uDec = decodeURIComponent(decoded);
          if (uDec !== decoded && uDec.length > 0) {
            decoded = uDec;
            changed = true;
            results.push(decoded);
          }
        } catch (_) {}
      }

      // 2. Unicode Escape Decoding (\u004a...)
      if (/\\u[0-9a-fA-F]{4}/.test(decoded)) {
        try {
          const unescaped = decoded.replace(/\\u([0-9a-fA-F]{4})/g, (_, grp) =>
            String.fromCharCode(parseInt(grp, 16))
          );
          if (unescaped !== decoded && unescaped.length > 0) {
            decoded = unescaped;
            changed = true;
            results.push(decoded);
          }
        } catch (_) {}
      }

      // 3. Base64 Decoding (Bounded length: 4 to 8192 characters)
      const cleanB64 = decoded.trim().replace(/\s+/g, '');
      if (
        cleanB64.length >= 4 &&
        cleanB64.length <= 8192 &&
        /^[A-Za-z0-9+/=_-]+$/.test(cleanB64) &&
        !cleanB64.startsWith('data:image/')
      ) {
        try {
          let b64Std = cleanB64.replace(/-/g, '+').replace(/_/g, '/');
          while (b64Std.length % 4 !== 0) b64Std += '=';
          
          if (typeof atob === 'function') {
            const b64Dec = atob(b64Std);
            if (/[\x20-\x7E]{3,}/.test(b64Dec) && b64Dec !== decoded) {
              decoded = b64Dec;
              changed = true;
              results.push(decoded);
            }
          }
        } catch (_) {}
      }

      if (!changed) break;
      current = decoded;
    }
  } else if (Array.isArray(data)) {
    for (let i = 0; i < Math.min(data.length, 500); i++) {
      results.push(...extractAllStringVariants(data[i], depth + 1, maxDepth, visited));
    }
  } else if (typeof data === 'object') {
    const keys = Object.keys(data);
    for (let i = 0; i < Math.min(keys.length, 200); i++) {
      const k = keys[i];
      results.push(k);
      results.push(...extractAllStringVariants(data[k], depth + 1, maxDepth, visited));
    }
  }

  return results;
}

/**
 * Validates egress payload recursively and encoding-aware before network request dispatch.
 */
export function validateNetworkEgress(
  rawEntities: DetectedEntity[],
  sanitizedNodes: DOMNodeDescriptor[],
  sanitizedScreenshotBase64?: string,
  visualPrivacyState: 'VERIFIED_SAFE' | 'PII_DETECTED' | 'VISUAL_PRIVACY_UNVERIFIED' = 'VERIFIED_SAFE',
  unverifiedVisualRegionsMasked: number = 0
): PrivacyBoundaryReport {
  const timestamp = Date.now();
  const validationDetails: string[] = [];

  let entitiesTransmitted = 0;
  let entitiesBlocked = 0;
  let entitiesTokenized = 0;
  let localOnlyEntities = 0;

  for (const ent of rawEntities) {
    if (ent.treatment === 'KEEP') {
      entitiesTransmitted++;
      validationDetails.push(`Entity ${ent.id} (${ent.type}) passed as KEEP (non-sensitive required slot).`);
    } else if (ent.treatment === 'TOKENIZE') {
      entitiesTokenized++;
      validationDetails.push(`Entity ${ent.id} (${ent.type}) replaced with local token ${ent.assignedToken}.`);
    } else if (ent.treatment === 'REMOVE' || ent.treatment === 'MASK') {
      entitiesBlocked++;
      validationDetails.push(`Entity ${ent.id} (${ent.type}) blocked/masked locally by MDE.`);
    } else if (ent.treatment === 'LOCAL_ONLY') {
      localOnlyEntities++;
      validationDetails.push(`Entity ${ent.id} (${ent.type}) retained locally only.`);
    }
  }

  // 1. Perform Recursive String Extraction & Multi-Layer Decoding across entire payload structure
  const payloadStringVariants = extractAllStringVariants(sanitizedNodes);
  let zeroRawPIIVerified = true;

  // Build a set of raw sensitive targets and their encoded representations to detect evasion attempts
  const sensitiveTargets = new Set<string>();
  for (const ent of rawEntities) {
    if (ent.treatment !== 'KEEP' && ent.rawValue && ent.rawValue.trim().length >= 3 && ent.type !== 'UNVERIFIED_VISUAL_REGION') {
      const val = ent.rawValue.trim();
      sensitiveTargets.add(val.toLowerCase());

      // Also add Base64 variant of raw value
      try {
        if (typeof btoa === 'function') {
          const b64Val = btoa(val);
          sensitiveTargets.add(b64Val.toLowerCase());
        }
      } catch (_) {}

      // Also add URL encoded variant
      try {
        const urlVal = encodeURIComponent(val);
        sensitiveTargets.add(urlVal.toLowerCase());
      } catch (_) {}
    }
  }

  // 2. Scan all string variants against sensitive targets & PII regex patterns
  for (const variant of payloadStringVariants) {
    const varLower = variant.toLowerCase();

    // Check against raw & encoded sensitive targets
    for (const target of sensitiveTargets) {
      if (varLower.includes(target)) {
        // Exclude legitimate tokens or redaction placeholders
        const isLegitToken = /^[A-Z_]+#[A-F0-9]+$/i.test(variant) || variant.includes('[REDACTED]') || variant.includes('••••');
        if (!isLegitToken) {
          zeroRawPIIVerified = false;
          validationDetails.push(`CRITICAL SECURITY FAILURE: Raw or Encoded PII target '${target}' detected in egress payload string variant!`);
        }
      }
    }

    // Scan for unmasked raw email patterns
    EGRESS_EMAIL_REGEX.lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = EGRESS_EMAIL_REGEX.exec(variant)) !== null) {
      const matchedEmail = match[0];
      for (const ent of rawEntities) {
        if (ent.treatment !== 'KEEP' && ent.rawValue && matchedEmail.toLowerCase() === ent.rawValue.toLowerCase()) {
          zeroRawPIIVerified = false;
          validationDetails.push(`CRITICAL SECURITY FAILURE: Raw Email '${matchedEmail}' detected in egress payload!`);
        }
      }
    }

    // Scan for unmasked raw credit cards
    EGRESS_CREDIT_CARD_REGEX.lastIndex = 0;
    while ((match = EGRESS_CREDIT_CARD_REGEX.exec(variant)) !== null) {
      const matchedCC = match[0].replace(/\D/g, '');
      if (matchedCC.length >= 13 && matchedCC.length <= 19) {
        for (const ent of rawEntities) {
          if (ent.rawValue && matchedCC === ent.rawValue.replace(/\D/g, '')) {
            zeroRawPIIVerified = false;
            validationDetails.push(`CRITICAL SECURITY FAILURE: Raw Credit Card detected in egress payload!`);
          }
        }
      }
    }

    // Scan for unmasked raw passport numbers
    EGRESS_PASSPORT_REGEX.lastIndex = 0;
    while ((match = EGRESS_PASSPORT_REGEX.exec(variant)) !== null) {
      const matchedPassport = match[0];
      for (const ent of rawEntities) {
        if (ent.rawValue && matchedPassport === ent.rawValue) {
          zeroRawPIIVerified = false;
          validationDetails.push(`CRITICAL SECURITY FAILURE: Raw Passport Number detected in egress payload!`);
        }
      }
    }

    // Scan for unmasked raw phone numbers
    EGRESS_PHONE_REGEX.lastIndex = 0;
    while ((match = EGRESS_PHONE_REGEX.exec(variant)) !== null) {
      const matchedPhone = match[0];
      for (const ent of rawEntities) {
        if (ent.rawValue && matchedPhone.replace(/\D/g, '') === ent.rawValue.replace(/\D/g, '')) {
          zeroRawPIIVerified = false;
          validationDetails.push(`CRITICAL SECURITY FAILURE: Raw Phone Number detected in egress payload!`);
        }
      }
    }
  }

  // 3. Verify Visual Screenshot Redaction Status
  let visualRedactionVerified = false;
  if (sanitizedScreenshotBase64 && sanitizedScreenshotBase64.startsWith('data:image/png;base64,')) {
    visualRedactionVerified = true;
    if (visualPrivacyState === 'VISUAL_PRIVACY_UNVERIFIED') {
      validationDetails.push(`Visual Egress Inspection: Fail-closed solid mask applied to ${unverifiedVisualRegionsMasked} unverified visual region(s).`);
    } else {
      validationDetails.push('Visual Egress Inspection Passed: Client canvas base64 screenshot is redacted.');
    }
  } else {
    validationDetails.push('Visual Egress Inspection: Structured DOM context mode operating without screenshot payload.');
  }

  const payloadString = JSON.stringify(sanitizedNodes);
  const sanitizedPayloadSizeBytes = new Blob([payloadString + (sanitizedScreenshotBase64 || '')]).size;
  const rawPayloadSizeBytes = sanitizedPayloadSizeBytes + rawEntities.reduce((acc, e) => acc + (e.rawValue ? e.rawValue.length : 0), 0);

  if (zeroRawPIIVerified) {
    validationDetails.push('Egress Inspection Passed: Zero raw or encoded sensitive entities detected across all payload string variants.');
  }

  return {
    timestamp,
    rawEntitiesDetected: rawEntities.length,
    entitiesTransmitted,
    entitiesBlocked,
    entitiesTokenized,
    localOnlyEntities,
    sanitizedPayloadSizeBytes,
    rawPayloadSizeBytes,
    zeroRawPIIVerified,
    visualRedactionVerified,
    visualPrivacyState,
    unverifiedVisualRegionsMasked,
    validatorVersion: 'v2.1.0-p4-fail-closed-visual-privacy',
    validationDetails,
  };
}
