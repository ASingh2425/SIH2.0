import { DetectedEntity } from '../types/privacy';
import { sanitizeBoundingBox } from '../privacy/visual_detector';

export class ClientCanvasRedactor {
  /**
   * Performs client-side canvas pixel obfuscation on sensitive and unverified bounding boxes.
   * Produces a sanitized base64 image representation with zero raw sensitive or unverified pixels.
   */
  public async redactViewportScreenshot(
    sensitiveEntities: DetectedEntity[],
    width: number = window.innerWidth || 1920,
    height: number = window.innerHeight || 1080
  ): Promise<{ sanitizedBase64: string; redactionCount: number }> {
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(width, 320);
    canvas.height = Math.max(height, 240);
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('[CanvasRedactor] Failed to acquire 2D canvas context');
    }

    // 1. Draw synthetic viewport background
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. Draw mock page structure
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(20, 20, canvas.width - 40, 60);

    ctx.fillStyle = '#38bdf8';
    ctx.font = '16px sans-serif';
    ctx.fillText('Browser Agent Active Tab Viewport', 40, 55);

    let redactionCount = 0;

    // 3. Perform Pixel Obfuscation / Solid Dark Masking on Sensitive & Unverified Bounding Boxes
    for (const ent of sensitiveEntities) {
      if (
        ent.treatment === 'REMOVE' ||
        ent.treatment === 'MASK' ||
        ent.treatment === 'TOKENIZE' ||
        ent.treatment === 'LOCAL_ONLY' ||
        ent.type === 'UNVERIFIED_VISUAL_REGION'
      ) {
        const rawBounds = ent.boundingRect || { x: 50, y: 100 + redactionCount * 40, width: 200, height: 30 };
        const bounds = sanitizeBoundingBox(rawBounds, canvas.width, canvas.height);
        if (!bounds) continue;

        // Apply dark solid fill pixel mask over sensitive or unverified bounding box
        ctx.fillStyle = '#020617'; // Solid dark fill
        ctx.fillRect(bounds.x, bounds.y, bounds.width, bounds.height);

        // Draw security border (red for detected PII, amber for unverified regions)
        const isUnverified = ent.type === 'UNVERIFIED_VISUAL_REGION';
        ctx.strokeStyle = isUnverified ? '#f59e0b' : '#ef4444';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(bounds.x, bounds.y, bounds.width, bounds.height);

        // Draw redacted label text on canvas image
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
    };
  }
}
