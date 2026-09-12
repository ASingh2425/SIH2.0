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
   * Multimodal Perception Fusion: Fuses DOM metadata + Regex patterns + Visual OCR/Canvas/SVG entities.
   */
  public async detectMultimodalEntities(
    nodes: DOMNodeDescriptor[],
    documentRoot?: Document
  ): Promise<{
    entities: DetectedEntity[];
    ocrLatencyMs: number;
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
    if (documentRoot || typeof document !== 'undefined') {
      const doc = documentRoot || document;
      const visualRes = await this.visualDetector.performVisualPerception(doc);
      detected.push(...visualRes.detectedVisualEntities);
      ocrLatencyMs = visualRes.latencyMs;
    }

    return {
      entities: this.deduplicateEntities(detected),
      ocrLatencyMs,
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

    // Credit Card / Financial Input
    if (
      lowerName.includes('card') ||
      lowerName.includes('cc') ||
      lowerId.includes('card') ||
      lowerName.includes('cvv') ||
      lowerName.includes('expiry')
    ) {
      entities.push({
        id: `entity_card_${node.nodeId}`,
        type: 'CREDIT_CARD',
        rawValue: value,
        maskedDisplay: '••••-••••-••••-••••',
        confidence: 0.96,
        sensitivity: 'CRITICAL',
        taskNecessity: 'NONE',
        treatment: 'REMOVE',
        nodeId: node.nodeId,
        boundingRect: node.bounds,
        detectionSource: 'DOM_ATTR',
      });
    }

    // Email Input Attribute
    if (lowerType === 'email' || lowerName.includes('email') || lowerId.includes('email')) {
      entities.push({
        id: `entity_email_attr_${node.nodeId}`,
        type: 'EMAIL',
        rawValue: value,
        maskedDisplay: this.maskEmail(value || 'user@example.com'),
        confidence: 0.95,
        sensitivity: 'HIGH',
        taskNecessity: 'HIGH',
        treatment: 'TOKENIZE',
        nodeId: node.nodeId,
        boundingRect: node.bounds,
        detectionSource: 'DOM_ATTR',
      });
    }

    // Name Field Attribute
    if (
      lowerName.includes('fname') ||
      lowerName.includes('lname') ||
      lowerName.includes('fullname') ||
      lowerName.includes('passenger') ||
      lowerName.includes('traveler') ||
      lowerId.includes('name')
    ) {
      entities.push({
        id: `entity_name_attr_${node.nodeId}`,
        type: 'NAME',
        rawValue: value,
        maskedDisplay: this.maskName(value || 'John Doe'),
        confidence: 0.92,
        sensitivity: 'MEDIUM',
        taskNecessity: 'HIGH',
        treatment: 'TOKENIZE',
        nodeId: node.nodeId,
        boundingRect: node.bounds,
        detectionSource: 'DOM_ATTR',
      });
    }

    return entities;
  }

  private scanTextWithRegex(text: string, nodeId: string): DetectedEntity[] {
    const entities: DetectedEntity[] = [];

    // Email Regex
    let match: RegExpExecArray | null;
    LocalPIIDetector.EMAIL_REGEX.lastIndex = 0;
    while ((match = LocalPIIDetector.EMAIL_REGEX.exec(text)) !== null) {
      entities.push({
        id: `entity_regex_email_${nodeId}_${match.index}`,
        type: 'EMAIL',
        rawValue: match[0],
        maskedDisplay: this.maskEmail(match[0]),
        confidence: 0.97,
        sensitivity: 'HIGH',
        taskNecessity: 'HIGH',
        treatment: 'TOKENIZE',
        nodeId,
        detectionSource: 'REGEX',
      });
    }

    // Passport Regex
    LocalPIIDetector.PASSPORT_REGEX.lastIndex = 0;
    while ((match = LocalPIIDetector.PASSPORT_REGEX.exec(text)) !== null) {
      entities.push({
        id: `entity_regex_passport_${nodeId}_${match.index}`,
        type: 'GOVT_ID',
        rawValue: match[0],
        maskedDisplay: '••••••••',
        confidence: 0.96,
        sensitivity: 'CRITICAL',
        taskNecessity: 'NONE',
        treatment: 'REMOVE',
        nodeId,
        detectionSource: 'REGEX',
      });
    }

    // Phone Regex
    LocalPIIDetector.PHONE_REGEX.lastIndex = 0;
    while ((match = LocalPIIDetector.PHONE_REGEX.exec(text)) !== null) {
      entities.push({
        id: `entity_regex_phone_${nodeId}_${match.index}`,
        type: 'PHONE',
        rawValue: match[0],
        maskedDisplay: '••••••••' + match[0].slice(-4),
        confidence: 0.94,
        sensitivity: 'HIGH',
        taskNecessity: 'MEDIUM',
        treatment: 'TOKENIZE',
        nodeId,
        detectionSource: 'REGEX',
      });
    }

    // Credit Card Regex
    LocalPIIDetector.CREDIT_CARD_REGEX.lastIndex = 0;
    while ((match = LocalPIIDetector.CREDIT_CARD_REGEX.exec(text)) !== null) {
      const cleanDigits = match[0].replace(/\D/g, '');
      if (cleanDigits.length >= 13 && cleanDigits.length <= 19) {
        entities.push({
          id: `entity_regex_cc_${nodeId}_${match.index}`,
          type: 'CREDIT_CARD',
          rawValue: match[0],
          maskedDisplay: '••••-••••-••••-' + cleanDigits.slice(-4),
          confidence: 0.98,
          sensitivity: 'CRITICAL',
          taskNecessity: 'NONE',
          treatment: 'REMOVE',
          nodeId,
          detectionSource: 'REGEX',
        });
      }
    }

    return entities;
  }

  private maskEmail(email: string): string {
    const parts = email.split('@');
    if (parts.length !== 2) return '***@***.com';
    const name = parts[0];
    const maskedName = name.length > 2 ? name[0] + '***' + name[name.length - 1] : '***';
    return `${maskedName}@${parts[1]}`;
  }

  private maskName(name: string): string {
    const parts = name.trim().split(/\s+/);
    return parts.map(p => (p.length > 1 ? p[0] + '***' : '*')).join(' ');
  }

  private deduplicateEntities(entities: DetectedEntity[]): DetectedEntity[] {
    const map = new Map<string, DetectedEntity>();
    for (const ent of entities) {
      const key = `${ent.nodeId || ent.id}_${ent.type}_${ent.rawValue}`;
      if (!map.has(key) || map.get(key)!.confidence < ent.confidence) {
        map.set(key, ent);
      }
    }
    return Array.from(map.values());
  }
}
