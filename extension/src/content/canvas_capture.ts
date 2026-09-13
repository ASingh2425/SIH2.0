import { DetectedEntity } from '../types/privacy';
import { sanitizeBoundingBox } from '../privacy/visual_detector';

export interface RedactionResult {
  sanitizedBase64: string;
  redactionCount: number;
  visualPrivacyState: 'VERIFIED_SAFE' | 'PII_DETECTED' | 'VISUAL_PRIVACY_UNVERIFIED';
  isRealCapture: boolean;
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
    _devicePixelRatio: number = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1
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

          // Solid dark fill pixel redaction
          ctx.fillStyle = '#020617';
          ctx.fillRect(bounds.x, bounds.y, bounds.width, bounds.height);

          // Security border & label
          const isUnverified = ent.type === 'UNVERIFIED_VISUAL_REGION';
          if (isUnverified) hasUnverifiedRegion = true;

          ctx.strokeStyle = isUnverified ? '#f59e0b' : '#ef4444';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(bounds.x, bounds.y, bounds.width, bounds.height);

          ctx.fillStyle = isUnverified ? '#fbbf24' : '#f87171';
          ctx.font = '10px monospace';
          const maskLabel = isUnverified ? '[UNVERIFIED REGION MASKED]' : `[REDACTED ${ent.type}]`;
          ctx.fillText(maskLabel, bounds.x + 4, bounds.y + Math.min(bounds.height / 2 + 3, bounds.height - 4));

          redactionCount++;
        }
      }

      const sanitizedBase64 = canvas.toDataURL('image/png');

      return {
        sanitizedBase64,
        redactionCount,
        visualPrivacyState: hasUnverifiedRegion ? 'VISUAL_PRIVACY_UNVERIFIED' : 'VERIFIED_SAFE',
        isRealCapture: true,
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
    devicePixelRatio: number = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1
  ): Promise<{ sanitizedBase64: string; redactionCount: number; visualPrivacyState: string; isRealCapture: boolean }> {
    if (rawScreenshotBase64 && rawScreenshotBase64.startsWith('data:image/')) {
      try {
        const res = await this.redactRealViewportScreenshot(
          rawScreenshotBase64,
          sensitiveEntities,
          width,
          height,
          devicePixelRatio
        );
        return {
          sanitizedBase64: res.sanitizedBase64,
          redactionCount: res.redactionCount,
          visualPrivacyState: res.visualPrivacyState,
          isRealCapture: res.isRealCapture,
        };
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
