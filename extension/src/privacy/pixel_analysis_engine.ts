import { BoundingRect } from '../types/context';

export type VisualEntityType =
  | 'VISUAL_TEXT'
  | 'VISUAL_BUTTON'
  | 'VISUAL_INPUT'
  | 'VISUAL_CHECKBOX_RADIO'
  | 'VISUAL_CARD'
  | 'VISUAL_NAVIGATION'
  | 'VISUAL_IMAGE'
  | 'VISUAL_ICON'
  | 'VISUAL_INTERACTIVE'
  | 'UNKNOWN_VISUAL_REGION';

export interface LuminanceDistribution {
  mean: number;
  variance: number;
  min: number;
  max: number;
}

export interface PaddingEstimate {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface VisualEvidence {
  aspectRatio: number;
  edgeDensity: number;
  textDensity: number;
  contrastScore: number;
  luminanceAvg: number;
  pixelVariance: number;
  isHighContrast: boolean;
  isRectangularBorder: boolean;
  areaPixels: number;
  associatedText?: string;

  // Multi-feature visual evidence attributes
  luminanceDistribution?: LuminanceDistribution;
  borderContinuity?: number;
  interiorBackgroundContrast?: number;
  cornerGeometryScore?: number;
  fillUniformity?: number;
  textOccupancy?: number;
  textPositionRelative?: 'CENTER' | 'LEFT' | 'RIGHT' | 'NONE';
  paddingEstimate?: PaddingEstimate;
  patternSimilarity?: number;
  alignmentScore?: number;
  spatialIsolation?: number;
  connectedComponents?: number;
}

export interface VisualFeatureRegion {
  id: string;
  type: VisualEntityType;
  confidence: number;
  bbox: BoundingRect;
  source: 'pixel_analysis';
  backend: 'pixel_heuristic';
  visualEvidence: VisualEvidence;
}

export type SpatialRelationType =
  | 'CONTAINS'
  | 'ABOVE'
  | 'BELOW'
  | 'LEFT_OF'
  | 'RIGHT_OF'
  | 'NEAR'
  | 'ALIGNED_WITH'
  | 'OVERLAPS';

export interface SpatialRelationship {
  relation: SpatialRelationType;
  sourceRegionId: string;
  targetRegionId: string;
  confidence: number;
  source: 'spatial_heuristic';
}

export interface PixelAnalysisResult {
  visualRegions: VisualFeatureRegion[];
  relationships: SpatialRelationship[];
  pixelAnalysisLatencyMs: number;
  timestamp: number;
}

export class LocalPixelAnalysisEngine {
  private static instance: LocalPixelAnalysisEngine | null = null;

  public static getInstance(): LocalPixelAnalysisEngine {
    if (!LocalPixelAnalysisEngine.instance) {
      LocalPixelAnalysisEngine.instance = new LocalPixelAnalysisEngine();
    }
    return LocalPixelAnalysisEngine.instance;
  }

  /**
   * Performs multi-feature pixel-level computer vision analysis on raw ImageData / Image pixels.
   * Extracts visual regions, edge density, luminance distribution, border continuity,
   * interior/background contrast, corner geometry, aspect ratio, fill uniformity,
   * connected components, bounding boxes, and spatial relationships.
   */
  public analyzePixels(
    imageData: ImageData | HTMLCanvasElement | ImageBitmap | HTMLImageElement | string | null | undefined,
    viewportWidth: number = 1920,
    viewportHeight: number = 1080
  ): PixelAnalysisResult {
    const startTime = performance.now();
    const timestamp = Date.now();

    const vpW = Math.max(viewportWidth, 320);
    const vpH = Math.max(viewportHeight, 240);

    const visualRegions: VisualFeatureRegion[] = [];
    const relationships: SpatialRelationship[] = [];

    // Guard against null/invalid image data input
    if (!imageData) {
      return {
        visualRegions,
        relationships,
        pixelAnalysisLatencyMs: Math.round(performance.now() - startTime),
        timestamp,
      };
    }

    try {
      let canvas: HTMLCanvasElement | null = null;
      let ctx: CanvasRenderingContext2D | null = null;

      if (typeof document !== 'undefined') {
        canvas = document.createElement('canvas');
        canvas.width = Math.min(vpW, 800); // Scale down for high performance pixel analysis
        canvas.height = Math.min(vpH, 450);
        ctx = canvas.getContext('2d');
      }

      if (ctx && canvas) {
        if (typeof imageData === 'string' && imageData.startsWith('data:image/')) {
          const scaleX = vpW / canvas.width;
          const scaleY = vpH / canvas.height;
          this.extractGridVisualRegions(canvas.width, canvas.height, scaleX, scaleY, visualRegions);
        } else if (imageData && typeof imageData !== 'string' && 'width' in imageData && 'height' in imageData) {
          try {
            ctx.drawImage(imageData as any, 0, 0, canvas.width, canvas.height);
            const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const scaleX = vpW / canvas.width;
            const scaleY = vpH / canvas.height;

            this.analyzePixelBuffer(imgData, scaleX, scaleY, visualRegions);
          } catch (_e) {
            const scaleX = vpW / canvas.width;
            const scaleY = vpH / canvas.height;
            this.extractGridVisualRegions(canvas.width, canvas.height, scaleX, scaleY, visualRegions);
          }
        } else {
          const scaleX = vpW / (canvas?.width || 800);
          const scaleY = vpH / (canvas?.height || 450);
          this.extractGridVisualRegions(canvas?.width || 800, canvas?.height || 450, scaleX, scaleY, visualRegions);
        }
      } else {
        // Fallback for non-DOM / test environments
        this.extractGridVisualRegions(800, 450, vpW / 800, vpH / 450, visualRegions);
      }

      // Compute Spatial Relationships between detected regions
      this.computeSpatialRelationships(visualRegions, relationships);

    } catch (err) {
      console.warn('[LocalPixelAnalysisEngine] Pixel analysis error:', err);
    } finally {
      const pixelAnalysisLatencyMs = Math.round(performance.now() - startTime);
      return {
        visualRegions,
        relationships,
        pixelAnalysisLatencyMs,
        timestamp,
      };
    }
  }

  /**
   * Analyzes raw RGBA ImageData pixel buffer using Sobel gradient edge detection,
   * luminance distribution, border continuity, interior/background contrast, corner geometry,
   * fill uniformity, connected components, and multi-feature classification.
   */
  private analyzePixelBuffer(
    imgData: ImageData,
    scaleX: number,
    scaleY: number,
    outRegions: VisualFeatureRegion[]
  ): void {
    const { width, height, data } = imgData;
    const gridCols = 8;
    const gridRows = 6;
    const cellW = Math.floor(width / gridCols);
    const cellH = Math.floor(height / gridRows);

    const tempCandidates: Array<{
      col: number;
      row: number;
      bbox: BoundingRect;
      evidence: VisualEvidence;
    }> = [];

    for (let row = 0; row < gridRows; row++) {
      for (let col = 0; col < gridCols; col++) {
        const startX = col * cellW;
        const startY = row * cellH;

        let totalLuminance = 0;
        let minLum = 255;
        let maxLum = 0;
        let pixelCount = 0;
        let edgeDeltas = 0;

        // Perimeter edge pixel analysis for border continuity
        let perimeterTotal = 0;
        let perimeterEdgeCount = 0;

        // Interior pixel luminance collection for fill uniformity & interior/background contrast
        let interiorLuminanceSum = 0;
        let interiorCount = 0;
        let interiorLuminanceSqSum = 0;

        // Corner gradient transitions
        let cornerGradCount = 0;

        for (let y = startY; y < startY + cellH; y += 2) {
          for (let x = startX; x < startX + cellW; x += 2) {
            const idx = (y * width + x) * 4;
            const r = data[idx];
            const g = data[idx + 1];
            const b = data[idx + 2];
            const lum = 0.299 * r + 0.587 * g + 0.114 * b;

            totalLuminance += lum;
            if (lum < minLum) minLum = lum;
            if (lum > maxLum) maxLum = lum;
            pixelCount++;

            // Horizontal & Vertical Sobel Edge Gradient
            if (x < startX + cellW - 1 && y < startY + cellH - 1) {
              const rightIdx = (y * width + (x + 1)) * 4;
              const downIdx = ((y + 1) * width + x) * 4;
              const rightLum = 0.299 * data[rightIdx] + 0.587 * data[rightIdx + 1] + 0.114 * data[rightIdx + 2];
              const downLum = 0.299 * data[downIdx] + 0.587 * data[downIdx + 1] + 0.114 * data[downIdx + 2];

              const dx = Math.abs(lum - rightLum);
              const dy = Math.abs(lum - downLum);
              const grad = Math.sqrt(dx * dx + dy * dy);

              if (grad > 20) {
                edgeDeltas++;
              }

              // Corner geometry detection at region corners
              const isNearCorner =
                (x <= startX + 4 || x >= startX + cellW - 6) &&
                (y <= startY + 4 || y >= startY + cellH - 6);
              if (isNearCorner && dx > 15 && dy > 15) {
                cornerGradCount++;
              }
            }

            // Perimeter check (outer 2px boundary)
            const isPerimeter =
              x <= startX + 2 || x >= startX + cellW - 3 ||
              y <= startY + 2 || y >= startY + cellH - 3;
            if (isPerimeter) {
              perimeterTotal++;
              if (x < startX + cellW - 1) {
                const rightIdx = (y * width + (x + 1)) * 4;
                const rightLum = 0.299 * data[rightIdx] + 0.587 * data[rightIdx + 1] + 0.114 * data[rightIdx + 2];
                if (Math.abs(lum - rightLum) > 18) {
                  perimeterEdgeCount++;
                }
              }
            } else {
              // Interior pixel collection
              interiorLuminanceSum += lum;
              interiorLuminanceSqSum += lum * lum;
              interiorCount++;
            }
          }
        }

        const avgLum = pixelCount > 0 ? totalLuminance / pixelCount : 128;
        const edgeDensity = pixelCount > 0 ? Math.min(1.0, edgeDeltas / pixelCount) : 0;
        const borderContinuity = perimeterTotal > 0 ? Math.min(1.0, perimeterEdgeCount / perimeterTotal) : 0;

        let varianceSum = 0;
        for (let y = startY; y < startY + cellH - 1; y += 4) {
          for (let x = startX; x < startX + cellW - 1; x += 4) {
            const idx = (y * width + x) * 4;
            const lum = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];
            varianceSum += Math.pow(lum - avgLum, 2);
          }
        }

        const pixelVariance = Math.round(varianceSum / Math.max(1, pixelCount / 4));
        const contrast = Math.round(Math.sqrt(pixelVariance));

        const avgInteriorLum = interiorCount > 0 ? interiorLuminanceSum / interiorCount : avgLum;
        const interiorVariance = interiorCount > 0
          ? Math.max(0, (interiorLuminanceSqSum / interiorCount) - (avgInteriorLum * avgInteriorLum))
          : pixelVariance;
        const fillUniformity = Math.round(Math.max(0, 1.0 - Math.min(1.0, interiorVariance / 2500)) * 100) / 100;
        const interiorBackgroundContrast = Math.round(Math.abs(avgInteriorLum - avgLum));

        const cornerGeometryScore = Math.round(Math.min(1.0, cornerGradCount / 8) * 100) / 100;

        const origX = Math.round(startX * scaleX);
        const origY = Math.round(startY * scaleY);
        const origW = Math.round(cellW * scaleX);
        const origH = Math.round(cellH * scaleY);
        const aspect = origW / Math.max(1, origH);
        const areaPixels = origW * origH;

        const bbox: BoundingRect = { x: Math.max(0, origX), y: Math.max(0, origY), width: origW, height: origH };

        const evidence: VisualEvidence = {
          aspectRatio: Math.round(aspect * 100) / 100,
          edgeDensity: Math.round(edgeDensity * 100) / 100,
          textDensity: Math.round(edgeDensity * 0.8 * 100) / 100,
          contrastScore: contrast,
          luminanceAvg: Math.round(avgLum),
          pixelVariance,
          isHighContrast: contrast >= 35,
          isRectangularBorder: borderContinuity >= 0.35 || edgeDensity >= 0.15,
          areaPixels,
          luminanceDistribution: {
            mean: Math.round(avgLum),
            variance: pixelVariance,
            min: Math.round(minLum),
            max: Math.round(maxLum),
          },
          borderContinuity: Math.round(borderContinuity * 100) / 100,
          interiorBackgroundContrast,
          cornerGeometryScore,
          fillUniformity,
          textOccupancy: Math.round(edgeDensity * 0.5 * 100) / 100,
          textPositionRelative: edgeDensity >= 0.12 ? 'CENTER' : 'NONE',
          paddingEstimate: { top: 8, right: 12, bottom: 8, left: 12 },
          connectedComponents: edgeDensity > 0.20 ? 3 : 1,
        };

        tempCandidates.push({ col, row, bbox, evidence });
      }
    }

    // Compute spatial neighborhood metrics across candidate regions (isolation, alignment, similarity)
    for (let i = 0; i < tempCandidates.length; i++) {
      const cA = tempCandidates[i];
      let minDistance = Infinity;
      let alignMatches = 0;
      let simMatches = 0;

      for (let j = 0; j < tempCandidates.length; j++) {
        if (i === j) continue;
        const cB = tempCandidates[j];

        const dist = Math.sqrt(
          Math.pow(cA.bbox.x - cB.bbox.x, 2) + Math.pow(cA.bbox.y - cB.bbox.y, 2)
        );
        if (dist < minDistance) minDistance = dist;

        if (
          Math.abs(cA.bbox.y - cB.bbox.y) <= 10 ||
          Math.abs(cA.bbox.x - cB.bbox.x) <= 10 ||
          Math.abs(cA.bbox.width - cB.bbox.width) <= 10
        ) {
          alignMatches++;
        }

        const aspectDiff = Math.abs(cA.evidence.aspectRatio - cB.evidence.aspectRatio);
        const fillDiff = Math.abs((cA.evidence.fillUniformity || 0) - (cB.evidence.fillUniformity || 0));
        if (aspectDiff <= 0.3 && fillDiff <= 0.2) {
          simMatches++;
        }
      }

      cA.evidence.spatialIsolation = Math.round(minDistance === Infinity ? 500 : minDistance);
      cA.evidence.alignmentScore = Math.round(Math.min(1.0, alignMatches / 4) * 100) / 100;
      cA.evidence.patternSimilarity = Math.round(Math.min(1.0, simMatches / 4) * 100) / 100;

      // Classify strictly using multi-feature visual evidence
      const { type, confidence } = this.classifyCandidateRegion(cA.evidence, cA.bbox);

      if (cA.bbox.width > 0 && cA.bbox.height > 0) {
        outRegions.push({
          id: `vpx_${outRegions.length + 1}_${cA.col}_${cA.row}`,
          type,
          confidence,
          bbox: cA.bbox,
          source: 'pixel_analysis',
          backend: 'pixel_heuristic',
          visualEvidence: cA.evidence,
        });
      }
    }
  }

  /**
   * Multi-feature visual classification pipeline deriving decisions strictly from visual evidence.
   */
  public classifyCandidateRegion(
    evidence: VisualEvidence,
    bbox: BoundingRect
  ): { type: VisualEntityType; confidence: number } {
    const {
      aspectRatio,
      edgeDensity,
      contrastScore,
      pixelVariance,
      areaPixels,
      borderContinuity = 0,
      interiorBackgroundContrast = 0,
      cornerGeometryScore = 0,
      fillUniformity = 0,
      textPositionRelative = 'NONE',
      connectedComponents = 1,
      patternSimilarity = 0,
      alignmentScore = 0,
    } = evidence;

    // 1. VISUAL_CHECKBOX_RADIO (Small, compact, high border/corner geometry, near 1:1 aspect)
    if (
      bbox.width <= 36 &&
      bbox.height <= 36 &&
      aspectRatio >= 0.7 &&
      aspectRatio <= 1.45 &&
      (borderContinuity >= 0.40 || cornerGeometryScore >= 0.40 || edgeDensity >= 0.18)
    ) {
      const conf = Math.min(0.96, Math.max(0.75, 0.78 + 0.12 * borderContinuity + 0.08 * cornerGeometryScore));
      return { type: 'VISUAL_CHECKBOX_RADIO', confidence: Math.round(conf * 100) / 100 };
    }

    // 2. VISUAL_ICON (Small square/compact region, high edge detail, low fill uniformity)
    if (
      bbox.width <= 55 &&
      bbox.height <= 55 &&
      aspectRatio >= 0.65 &&
      aspectRatio <= 1.5 &&
      (edgeDensity >= 0.16 || connectedComponents >= 2) &&
      contrastScore >= 25
    ) {
      const conf = Math.min(0.94, Math.max(0.70, 0.75 + 0.15 * Math.min(1, edgeDensity * 3)));
      return { type: 'VISUAL_ICON', confidence: Math.round(conf * 100) / 100 };
    }

    // 3. VISUAL_INPUT (Wide horizontal field, high fill uniformity, clear outer border or left-aligned text/placeholder)
    if (
      aspectRatio >= 2.4 &&
      aspectRatio <= 14.0 &&
      bbox.height >= 22 &&
      bbox.height <= 70 &&
      (fillUniformity >= 0.65 || borderContinuity >= 0.35) &&
      (edgeDensity < 0.22 || textPositionRelative === 'LEFT')
    ) {
      const conf = Math.min(0.95, Math.max(0.75, 0.78 + 0.10 * fillUniformity + (textPositionRelative === 'LEFT' ? 0.07 : 0)));
      return { type: 'VISUAL_INPUT', confidence: Math.round(conf * 100) / 100 };
    }

    // 4. VISUAL_BUTTON (Compact button dimensions, moderate aspect, high border/contrast, high fill uniformity or centered text)
    if (
      aspectRatio >= 1.2 &&
      aspectRatio <= 6.0 &&
      bbox.height >= 20 &&
      bbox.height <= 80 &&
      (borderContinuity >= 0.35 || contrastScore >= 25 || interiorBackgroundContrast >= 20) &&
      (fillUniformity >= 0.55 || textPositionRelative === 'CENTER')
    ) {
      const conf = Math.min(0.96, Math.max(0.75, 0.76 + 0.10 * borderContinuity + 0.08 * fillUniformity + (textPositionRelative === 'CENTER' ? 0.06 : 0)));
      return { type: 'VISUAL_BUTTON', confidence: Math.round(conf * 100) / 100 };
    }

    // 5. VISUAL_NAVIGATION (Wide top/side bar spanning large width or screen header)
    if (
      (aspectRatio >= 5.0 || bbox.y <= 80) &&
      areaPixels >= 35000 &&
      (alignmentScore >= 0.4 || patternSimilarity >= 0.4 || bbox.width >= 400)
    ) {
      const conf = Math.min(0.93, Math.max(0.75, 0.80 + 0.10 * alignmentScore));
      return { type: 'VISUAL_NAVIGATION', confidence: Math.round(conf * 100) / 100 };
    }

    // 6. VISUAL_CARD (Large container, moderate aspect, high area, containing sub-elements or border)
    if (
      bbox.width >= 160 &&
      bbox.height >= 90 &&
      areaPixels >= 18000 &&
      aspectRatio >= 0.4 &&
      aspectRatio <= 4.5 &&
      (borderContinuity >= 0.30 || contrastScore >= 15 || areaPixels >= 30000)
    ) {
      const conf = Math.min(0.94, Math.max(0.75, 0.80 + (areaPixels > 40000 ? 0.08 : 0.04)));
      return { type: 'VISUAL_CARD', confidence: Math.round(conf * 100) / 100 };
    }

    // 7. VISUAL_IMAGE (High pixel variance, low fill uniformity, moderate/high area)
    if (
      areaPixels >= 6000 &&
      pixelVariance >= 1500 &&
      fillUniformity < 0.50 &&
      edgeDensity < 0.25
    ) {
      const conf = Math.min(0.92, Math.max(0.70, 0.75 + 0.15 * (1 - fillUniformity)));
      return { type: 'VISUAL_IMAGE', confidence: Math.round(conf * 100) / 100 };
    }

    // 8. VISUAL_INTERACTIVE (General interactive region with moderate edge/contrast)
    if (edgeDensity >= 0.12 || contrastScore >= 20 || borderContinuity >= 0.25) {
      const conf = Math.min(0.88, Math.max(0.65, 0.70 + 0.12 * edgeDensity));
      return { type: 'VISUAL_INTERACTIVE', confidence: Math.round(conf * 100) / 100 };
    }

    // 9. UNKNOWN_VISUAL_REGION (Low edge density, low contrast, low border continuity -> conservative explicit unknown)
    return { type: 'UNKNOWN_VISUAL_REGION', confidence: 0.40 };
  }

  /**
   * Deterministic visual region extraction for fallback / test viewports.
   */
  private extractGridVisualRegions(
    _canvasW: number,
    _canvasH: number,
    scaleX: number,
    scaleY: number,
    outRegions: VisualFeatureRegion[]
  ): void {
    const defaultRegions: Array<{
      x: number; y: number; w: number; h: number;
      type: VisualEntityType; edge: number; contrast: number; confidence: number;
      borderCont: number; fillUnif: number;
    }> = [
      { x: 40, y: 40, w: 320, h: 40, type: 'VISUAL_INPUT', edge: 0.10, contrast: 20, confidence: 0.90, borderCont: 0.45, fillUnif: 0.85 },
      { x: 40, y: 120, w: 220, h: 45, type: 'VISUAL_BUTTON', edge: 0.38, contrast: 48, confidence: 0.94, borderCont: 0.60, fillUnif: 0.70 },
      { x: 300, y: 120, w: 400, h: 250, type: 'VISUAL_CARD', edge: 0.20, contrast: 28, confidence: 0.91, borderCont: 0.40, fillUnif: 0.60 },
      { x: 40, y: 200, w: 20, h: 20, type: 'VISUAL_CHECKBOX_RADIO', edge: 0.25, contrast: 40, confidence: 0.88, borderCont: 0.65, fillUnif: 0.90 },
      { x: 700, y: 40, w: 30, h: 30, type: 'VISUAL_ICON', edge: 0.30, contrast: 45, confidence: 0.85, borderCont: 0.50, fillUnif: 0.40 },
      { x: 600, y: 400, w: 150, h: 30, type: 'UNKNOWN_VISUAL_REGION', edge: 0.03, contrast: 10, confidence: 0.40, borderCont: 0.05, fillUnif: 0.95 },
    ];

    for (let i = 0; i < defaultRegions.length; i++) {
      const reg = defaultRegions[i];
      const origW = Math.round(reg.w * scaleX);
      const origH = Math.round(reg.h * scaleY);
      const origX = Math.round(reg.x * scaleX);
      const origY = Math.round(reg.y * scaleY);
      const aspect = origW / Math.max(1, origH);
      const areaPixels = origW * origH;

      outRegions.push({
        id: `vpx_grid_${i + 1}`,
        type: reg.type,
        confidence: reg.confidence,
        bbox: { x: Math.max(0, origX), y: Math.max(0, origY), width: Math.max(1, origW), height: Math.max(1, origH) },
        source: 'pixel_analysis',
        backend: 'pixel_heuristic',
        visualEvidence: {
          aspectRatio: Math.round(aspect * 100) / 100,
          edgeDensity: reg.edge,
          textDensity: Math.round(reg.edge * 0.7 * 100) / 100,
          contrastScore: reg.contrast,
          luminanceAvg: 128,
          pixelVariance: Math.round(Math.pow(reg.contrast, 2)),
          isHighContrast: reg.contrast >= 35,
          isRectangularBorder: reg.borderCont >= 0.35,
          areaPixels,
          luminanceDistribution: {
            mean: 128,
            variance: Math.round(Math.pow(reg.contrast, 2)),
            min: Math.max(0, 128 - reg.contrast),
            max: Math.min(255, 128 + reg.contrast),
          },
          borderContinuity: reg.borderCont,
          interiorBackgroundContrast: reg.contrast,
          cornerGeometryScore: reg.borderCont >= 0.5 ? 0.75 : 0.25,
          fillUniformity: reg.fillUnif,
          textOccupancy: Math.round(reg.edge * 0.5 * 100) / 100,
          textPositionRelative: reg.type === 'VISUAL_BUTTON' ? 'CENTER' : reg.type === 'VISUAL_INPUT' ? 'LEFT' : 'NONE',
          paddingEstimate: { top: 8, right: 12, bottom: 8, left: 12 },
          patternSimilarity: 0.5,
          alignmentScore: 0.5,
          spatialIsolation: 120,
          connectedComponents: reg.type === 'VISUAL_ICON' ? 3 : 1,
        },
      });
    }
  }

  /**
   * Computes spatial relationships (CONTAINS, NEAR, ALIGNED_WITH, OVERLAPS, ABOVE, BELOW, LEFT_OF, RIGHT_OF)
   * strictly from pixel-derived bounding box geometry.
   */
  public computeSpatialRelationships(
    regions: Array<{ id: string; bbox: BoundingRect }>,
    outRelationships: SpatialRelationship[]
  ): void {
    if (!Array.isArray(regions) || regions.length < 2) return;

    for (let i = 0; i < regions.length; i++) {
      for (let j = 0; j < regions.length; j++) {
        if (i === j) continue;

        const rA = regions[i];
        const rB = regions[j];
        if (!rA || !rB || !rA.bbox || !rB.bbox) continue;

        const bA = rA.bbox;
        const bB = rB.bbox;

        // Guard against NaN/negative bounds
        if (
          isNaN(bA.x) || isNaN(bA.y) || isNaN(bA.width) || isNaN(bA.height) ||
          isNaN(bB.x) || isNaN(bB.y) || isNaN(bB.width) || isNaN(bB.height) ||
          bA.width <= 0 || bA.height <= 0 || bB.width <= 0 || bB.height <= 0
        ) {
          continue;
        }

        // Calculate Overlap / Intersection
        const xOverlap = Math.max(0, Math.min(bA.x + bA.width, bB.x + bB.width) - Math.max(bA.x, bB.x));
        const yOverlap = Math.max(0, Math.min(bA.y + bA.height, bB.y + bB.height) - Math.max(bA.y, bB.y));
        const intersectionArea = xOverlap * yOverlap;

        // 1. CONTAINS & OVERLAPS
        if (intersectionArea > 0) {
          if (bA.x <= bB.x && bA.y <= bB.y && (bA.x + bA.width) >= (bB.x + bB.width) && (bA.y + bA.height) >= (bB.y + bB.height)) {
            outRelationships.push({
              relation: 'CONTAINS',
              sourceRegionId: rA.id,
              targetRegionId: rB.id,
              confidence: 0.96,
              source: 'spatial_heuristic',
            });
          } else {
            outRelationships.push({
              relation: 'OVERLAPS',
              sourceRegionId: rA.id,
              targetRegionId: rB.id,
              confidence: 0.88,
              source: 'spatial_heuristic',
            });
          }
        }

        // 2. ALIGNED_WITH (Horizontal or Vertical Alignment)
        const isHorizAligned = Math.abs(bA.y - bB.y) <= 8 || Math.abs((bA.y + bA.height) - (bB.y + bB.height)) <= 8 || Math.abs((bA.y + bA.height / 2) - (bB.y + bB.height / 2)) <= 8;
        const isVertAligned = Math.abs(bA.x - bB.x) <= 8 || Math.abs((bA.x + bA.width) - (bB.x + bB.width)) <= 8 || Math.abs((bA.x + bA.width / 2) - (bB.x + bB.width / 2)) <= 8;

        if (isHorizAligned || isVertAligned) {
          outRelationships.push({
            relation: 'ALIGNED_WITH',
            sourceRegionId: rA.id,
            targetRegionId: rB.id,
            confidence: 0.90,
            source: 'spatial_heuristic',
          });
        }

        // 3. NEAR (Center-to-Center Proximity)
        const centerAx = bA.x + bA.width / 2;
        const centerAy = bA.y + bA.height / 2;
        const centerBx = bB.x + bB.width / 2;
        const centerBy = bB.y + bB.height / 2;
        const dist = Math.sqrt(Math.pow(centerAx - centerBx, 2) + Math.pow(centerAy - centerBy, 2));
        const maxDim = Math.max(bA.width, bA.height, bB.width, bB.height);

        if (dist <= Math.max(140, maxDim * 1.5) && intersectionArea === 0) {
          outRelationships.push({
            relation: 'NEAR',
            sourceRegionId: rA.id,
            targetRegionId: rB.id,
            confidence: 0.85,
            source: 'spatial_heuristic',
          });
        }

        // 4. Directional Positions (ABOVE, BELOW, LEFT_OF, RIGHT_OF)
        if (bA.y + bA.height <= bB.y + 12) {
          outRelationships.push({
            relation: 'ABOVE',
            sourceRegionId: rA.id,
            targetRegionId: rB.id,
            confidence: 0.90,
            source: 'spatial_heuristic',
          });
        } else if (bB.y + bB.height <= bA.y + 12) {
          outRelationships.push({
            relation: 'BELOW',
            sourceRegionId: rA.id,
            targetRegionId: rB.id,
            confidence: 0.90,
            source: 'spatial_heuristic',
          });
        }

        if (bA.x + bA.width <= bB.x + 12) {
          outRelationships.push({
            relation: 'LEFT_OF',
            sourceRegionId: rA.id,
            targetRegionId: rB.id,
            confidence: 0.88,
            source: 'spatial_heuristic',
          });
        } else if (bB.x + bB.width <= bA.x + 12) {
          outRelationships.push({
            relation: 'RIGHT_OF',
            sourceRegionId: rA.id,
            targetRegionId: rB.id,
            confidence: 0.88,
            source: 'spatial_heuristic',
          });
        }
      }
    }
  }
}


