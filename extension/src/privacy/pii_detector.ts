import { DetectedEntity } from '../types/privacy';
import { DOMNodeDescriptor } from '../types/context';
import { LocalVisualDetector } from './visual_detector';

export class LocalPIIDetector {
  private static EMAIL_REGEX = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
  private static PHONE_REGEX = /\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g;
  private static CREDIT_CARD_REGEX = /\b(?:\d[ -]*?){13,16}\b/g;
  private static PASSPORT_REGEX = /\b[A-PR-WYa-pr-wy]\d{7}\b/g;

  private visualDetector = new LocalVisualDetector();

  public getVisualDetector(): LocalVisualDetector {
    return this.visualDetector;
  }

  /**
   * Multimodal Perception Fusion: Fuses DOM metadata + Regex patterns + Visual OCR / Canvas / SVG entities.
   */
  public async detectMultimodalEntities(
    nodes: DOMNodeDescriptor[],
    documentRoot?: Document,
    rawPixelInput?: HTMLCanvasElement | ImageData | ImageBitmap | HTMLImageElement | string
  ): Promise<{
    entities: DetectedEntity[];
    ocrLatencyMs: number;
    visualPrivacyState: 'VERIFIED_SAFE' | 'PII_DETECTED' | 'VISUAL_PRIVACY_UNVERIFIED';
    unverifiedVisualRegionsMasked: number;
    backendUsed: string;
    modelId: string;
  }> {
    const detected: DetectedEntity[] = [];

    // 1. DOM Attribute & HTML Metadata Inspection
    for (const node of nodes) {
      const attrEntities = this.inspectNodeAttributes(node);
      detected.push(...attrEntities);

      // 2. Regex Content Scan
      const textToScan = node.text || node.sanitizedValue || '';
      if (textToScan.length > 0) {
        const regexEntities = this.scanTextWithRegex(textToScan, node.nodeId);
        detected.push(...regexEntities);
      }
    }

    // 3. Visual OCR & Image/Canvas/SVG Perception
    let ocrLatencyMs = 0;
    let visualPrivacyState: 'VERIFIED_SAFE' | 'PII_DETECTED' | 'VISUAL_PRIVACY_UNVERIFIED' = 'VERIFIED_SAFE';
    let unverifiedVisualRegionsMasked = 0;
    let backendUsed = 'dom_fallback';
    let modelId = 'Canvas2D-Deterministic-OCR-Engine';

    if (documentRoot || typeof document !== 'undefined' || rawPixelInput) {
      const doc = documentRoot || (typeof document !== 'undefined' ? document : (null as any));
      const visualRes = await this.visualDetector.performVisualPerception(doc, rawPixelInput);
      detected.push(...visualRes.detectedVisualEntities);
      ocrLatencyMs = visualRes.latencyMs;
      visualPrivacyState = visualRes.visualPrivacyState;
      unverifiedVisualRegionsMasked = visualRes.unverifiedVisualRegionsMasked;
      backendUsed = visualRes.backendUsed;
      modelId = visualRes.modelId;
    }

    return {
      entities: this.deduplicateEntities(detected),
      ocrLatencyMs,
      visualPrivacyState,
      unverifiedVisualRegionsMasked,
      backendUsed,
      modelId,
    };
  }

  private inspectNodeAttributes(node: DOMNodeDescriptor): DetectedEntity[] {
    const entities: DetectedEntity[] = [];
    const lowerType = (node.inputType || '').toLowerCase();
    const lowerName = (node.nameAttr || '').toLowerCase();
    const lowerId = (node.idAttr || '').toLowerCase();
    const value = node.text || '';

    // Password Inspection
    if (lowerType === 'password' || lowerName.includes('pass') || lowerId.includes('pass')) {
      entities.push({
        id: `entity_pass_${node.nodeId}`,
        type: 'PASSWORD',
        rawValue: value,
        maskedDisplay: '••••••••',
        confidence: 0.99,
        sensitivity: 'CRITICAL',
        taskNecessity: 'NONE',
        treatment: 'REMOVE',
        nodeId: node.nodeId,
        boundingRect: node.bounds,
        detectionSource: 'DOM_ATTR',
      });
    }

    // Passport Inspection
    if (lowerName.includes('passport') || lowerId.includes('passport')) {
      entities.push({
        id: `entity_passport_${node.nodeId}`,
        type: 'GOVT_ID',
        rawValue: value,
        maskedDisplay: '••••••••',
        confidence: 0.98,
        sensitivity: 'CRITICAL',
        taskNecessity: 'NONE',
        treatment: 'REMOVE',
        nodeId: node.nodeId,
        boundingRect: node.bounds,
        detectionSource: 'DOM_ATTR',
      });
    }

    // Credit Card Inspection
    if (lowerName.includes('card') || lowerId.includes('card') || lowerName.includes('cc')) {
      entities.push({
        id: `entity_cc_${node.nodeId}`,
        type: 'CREDIT_CARD',
        rawValue: value,
        maskedDisplay: '••••-••••-••••-••••',
        confidence: 0.95,
        sensitivity: 'CRITICAL',
        taskNecessity: 'NONE',
        treatment: 'REMOVE',
        nodeId: node.nodeId,
        boundingRect: node.bounds,
        detectionSource: 'DOM_ATTR',
      });
    }

    return entities;
  }

  private scanTextWithRegex(text: string, nodeId: string): DetectedEntity[] {
    const entities: DetectedEntity[] = [];

    // Email
    LocalPIIDetector.EMAIL_REGEX.lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = LocalPIIDetector.EMAIL_REGEX.exec(text)) !== null) {
      entities.push({
        id: `entity_email_${nodeId}_${match.index}`,
        type: 'EMAIL',
        rawValue: match[0],
        maskedDisplay: match[0][0] + '***@***.com',
        confidence: 0.97,
        sensitivity: 'HIGH',
        taskNecessity: 'HIGH',
        treatment: 'TOKENIZE',
        nodeId,
        detectionSource: 'REGEX',
      });
    }

    // Phone
    LocalPIIDetector.PHONE_REGEX.lastIndex = 0;
    while ((match = LocalPIIDetector.PHONE_REGEX.exec(text)) !== null) {
      entities.push({
        id: `entity_phone_${nodeId}_${match.index}`,
        type: 'PHONE',
        rawValue: match[0],
        maskedDisplay: '••••••••' + match[0].slice(-4),
        confidence: 0.93,
        sensitivity: 'HIGH',
        taskNecessity: 'MEDIUM',
        treatment: 'TOKENIZE',
        nodeId,
        detectionSource: 'REGEX',
      });
    }

    // Credit Card
    LocalPIIDetector.CREDIT_CARD_REGEX.lastIndex = 0;
    while ((match = LocalPIIDetector.CREDIT_CARD_REGEX.exec(text)) !== null) {
      const clean = match[0].replace(/\D/g, '');
      if (clean.length >= 13 && clean.length <= 19) {
        entities.push({
          id: `entity_cc_${nodeId}_${match.index}`,
          type: 'CREDIT_CARD',
          rawValue: match[0],
          maskedDisplay: '••••-••••-••••-' + clean.slice(-4),
          confidence: 0.98,
          sensitivity: 'CRITICAL',
          taskNecessity: 'NONE',
          treatment: 'REMOVE',
          nodeId,
          detectionSource: 'REGEX',
        });
      }
    }

    // Passport
    LocalPIIDetector.PASSPORT_REGEX.lastIndex = 0;
    while ((match = LocalPIIDetector.PASSPORT_REGEX.exec(text)) !== null) {
      entities.push({
        id: `entity_passport_${nodeId}_${match.index}`,
        type: 'GOVT_ID',
        rawValue: match[0],
        maskedDisplay: '••••••••',
        confidence: 0.95,
        sensitivity: 'CRITICAL',
        taskNecessity: 'NONE',
        treatment: 'REMOVE',
        nodeId,
        detectionSource: 'REGEX',
      });
    }

    return entities;
  }

  private deduplicateEntities(entities: DetectedEntity[]): DetectedEntity[] {
    const seen = new Map<string, DetectedEntity>();

    for (const ent of entities) {
      const key = `${ent.type}_${ent.rawValue.trim().toLowerCase()}_${ent.boundingRect?.x || 0}_${ent.boundingRect?.y || 0}`;
      if (!seen.has(key)) {
        seen.set(key, ent);
      } else {
        const existing = seen.get(key)!;
        if (ent.confidence > existing.confidence) {
          seen.set(key, ent);
        }
      }
    }

    return Array.from(seen.values());
  }
}
