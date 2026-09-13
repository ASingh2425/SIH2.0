import { DetectedEntity } from '../types/privacy';
import { ImageEgressAttestation } from '../types/context';
import { sanitizeBoundingBox } from '../privacy/visual_detector';

export interface RedactionResult {
  sanitizedBase64: string;
  redactionCount: number;
  visualPrivacyState: 'VERIFIED_SAFE' | 'PII_DETECTED' | 'VISUAL_PRIVACY_UNVERIFIED';
  isRealCapture: boolean;
  attestation?: ImageEgressAttestation;
}

export function computeStringDigest(str: string): string {
  if (!str) return '';
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return 'digest_' + Math.abs(hash).toString(16) + '_' + str.length;
}

export class ClientCanvasRedactor {
  /**
   * Redacts a REAL browser viewport screenshot captured via chrome.tabs.captureVisibleTab.
   * Loads the real captured base64 image, scales to viewport coordinates, applies solid
   * dark fill (#020617) over all sensitive PII and unverified visual regions, and purges
   * in-memory raw image references immediately after export.
   */
  public async redactRealViewportScreenshot(
    rawBase64Image: string,
    sensitiveEntities: DetectedEntity[],
    viewportWidth: number = typeof window !== 'undefined' ? window.innerWidth : 1920,
    viewportHeight: number = typeof window !== 'undefined' ? window.innerHeight : 1080,
    _devicePixelRatio: number = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1,
    taskId: string = 'task_default',
    captureId: string = 'cap_default',
    perceptionId: string = 'percept_default'
  ): Promise<RedactionResult> {
    // 0. Validate raw input screenshot string (FAIL-CLOSED)
    if (!rawBase64Image || typeof rawBase64Image !== 'string' || !rawBase64Image.startsWith('data:image/')) {
      return {
        sanitizedBase64: '',
        redactionCount: 0,
        visualPrivacyState: 'VISUAL_PRIVACY_UNVERIFIED',
        isRealCapture: false,
      };
    }

    const vpW = Math.max(viewportWidth, 320);
    const vpH = Math.max(viewportHeight, 240);

    const canvas = document.createElement('canvas');
    canvas.width = vpW;
    canvas.height = vpH;
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      return {
        sanitizedBase64: '',
        redactionCount: 0,
        visualPrivacyState: 'VISUAL_PRIVACY_UNVERIFIED',
        isRealCapture: false,
      };
    }

    // 1. Load real browser viewport screenshot into Image element
    const img = new Image();
    try {
      const imgLoaded = await new Promise<boolean>(resolve => {
        img.onload = () => resolve(true);
        img.onerror = () => resolve(false);
        img.src = rawBase64Image;
      });

      if (!imgLoaded || img.width === 0 || img.height === 0) {
        return {
          sanitizedBase64: '',
          redactionCount: 0,
          visualPrivacyState: 'VISUAL_PRIVACY_UNVERIFIED',
          isRealCapture: false,
        };
      }

      // 2. Render real image onto canvas scaled to CSS viewport dimensions
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      let redactionCount = 0;
      let hasUnverifiedRegion = false;

      // 3. Apply Solid Dark Fill (#020617) over all sensitive PII and unverified visual regions
      for (const ent of sensitiveEntities) {
        if (
          ent.treatment === 'REMOVE' ||
          ent.treatment === 'MASK' ||
          ent.treatment === 'TOKENIZE' ||
          ent.treatment === 'LOCAL_ONLY' ||
          ent.type === 'UNVERIFIED_VISUAL_REGION'
        ) {
          const rawBounds = ent.boundingRect || { x: 0, y: 0, width: canvas.width, height: canvas.height };
          const bounds = sanitizeBoundingBox(rawBounds, canvas.width, canvas.height);
          if (!bounds) continue;

          // 2px tight safety margin padding to guarantee complete coverage of antialiased text edges
          const pad = 2;
          const padX = Math.max(0, bounds.x - pad);
          const padY = Math.max(0, bounds.y - pad);
          const padW = Math.min(canvas.width - padX, bounds.width + pad * 2);
          const padH = Math.min(canvas.height - padY, bounds.height + pad * 2);

          ctx.save();
          // Solid dark fill pixel redaction
          ctx.fillStyle = '#020617';
          ctx.fillRect(padX, padY, padW, padH);

          // Security border & label
          const isUnverified = ent.type === 'UNVERIFIED_VISUAL_REGION';
          if (isUnverified) hasUnverifiedRegion = true;

          ctx.strokeStyle = isUnverified ? '#f59e0b' : '#ef4444';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(padX, padY, padW, padH);

          // Clip label strictly inside redacted box to prevent bleeding onto benign UI
          ctx.beginPath();
          ctx.rect(padX, padY, padW, padH);
          ctx.clip();

          ctx.fillStyle = isUnverified ? '#fbbf24' : '#f87171';
          ctx.font = '10px monospace';
          const maskLabel = isUnverified ? '[UNVERIFIED REGION MASKED]' : `[REDACTED ${ent.type}]`;
          ctx.fillText(maskLabel, padX + 4, padY + Math.min(padH / 2 + 3, padH - 4));
          ctx.restore();

          redactionCount++;
        }
      }

      const sanitizedBase64 = canvas.toDataURL('image/png');
      const sanitizedImageDigest = computeStringDigest(sanitizedBase64);

      const attestation: ImageEgressAttestation = {
        captureId,
        taskId,
        sanitizedImageDigest,
        perceptionId,
        redactionCount,
        timestamp: Date.now(),
        status: hasUnverifiedRegion ? 'UNVERIFIED' : 'SANITIZED',
      };

      return {
        sanitizedBase64,
        redactionCount,
        visualPrivacyState: hasUnverifiedRegion ? 'VISUAL_PRIVACY_UNVERIFIED' : 'VERIFIED_SAFE',
        isRealCapture: true,
        attestation,
      };
    } catch (_err) {
      // FAIL-CLOSED ON REDACTION EXCEPTION
      return {
        sanitizedBase64: '',
        redactionCount: 0,
        visualPrivacyState: 'VISUAL_PRIVACY_UNVERIFIED',
        isRealCapture: false,
      };
    } finally {
      // 4. In-Memory Reference Discarding / Zeroing
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
      canvas.width = 0;
      canvas.height = 0;
      img.src = '';
    }
  }

  /**
   * Main entry point for viewport screenshot redaction.
   * If `rawScreenshotBase64` is provided, performs real viewport screenshot redaction.
   * If missing or invalid, FAILS CLOSED (returns visualPrivacyState: 'VISUAL_PRIVACY_UNVERIFIED').
   */
  public async redactViewportScreenshot(
    sensitiveEntities: DetectedEntity[],
    width: number = typeof window !== 'undefined' ? window.innerWidth : 1920,
    height: number = typeof window !== 'undefined' ? window.innerHeight : 1080,
    rawScreenshotBase64?: string,
    devicePixelRatio: number = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1,
    taskId: string = 'task_default',
    captureId: string = 'cap_default',
    perceptionId: string = 'percept_default'
  ): Promise<RedactionResult> {
    if (rawScreenshotBase64 && rawScreenshotBase64.startsWith('data:image/')) {
      try {
        const res = await this.redactRealViewportScreenshot(
          rawScreenshotBase64,
          sensitiveEntities,
          width,
          height,
          devicePixelRatio,
          taskId,
          captureId,
          perceptionId
        );
        return res;
      } catch (_err) {
        return {
          sanitizedBase64: '',
          redactionCount: 0,
          visualPrivacyState: 'VISUAL_PRIVACY_UNVERIFIED',
          isRealCapture: false,
        };
      }
    }

    // FAIL-CLOSED: No raw real screenshot supplied. Return unverified state with NO egress image.
    return {
      sanitizedBase64: '',
      redactionCount: 0,
      visualPrivacyState: 'VISUAL_PRIVACY_UNVERIFIED',
      isRealCapture: false,
    };
  }

  /**
   * Explicitly labeled synthetic illustration generator for UI / Demo purposes ONLY.
   * MUST NEVER be treated or transmitted as an actual captured webpage screenshot payload.
   */
  public generateExplicitSyntheticIllustrationDemoOnly(
    width: number = 1920,
    height: number = 1080
  ): string {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#f59e0b';
    ctx.font = '16px sans-serif';
    ctx.fillText('DEMO ILLUSTRATION ONLY — NOT A REAL SCREENSHOT', 40, 55);
    const url = canvas.toDataURL('image/png');
    canvas.width = 0;
    canvas.height = 0;
    return url;
  }
}
