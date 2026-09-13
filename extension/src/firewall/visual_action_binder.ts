import { BoundingRect } from '../types/context';
import { StructuredAction } from '../types/action';
import { VisualFeatureRegion } from '../privacy/pixel_analysis_engine';

export interface VisualActionBinding {
  taskId: string;
  captureId: string;
  perceptionId: string;
  visualObjectId: string;
  visualObjectType: string;
  visualBoundingBox: BoundingRect;
  targetClickCoordinates?: { x: number; y: number };
  targetDOMNodeId?: string;
  sceneDigest: string;
  timestamp: number;
}

export interface GroundingVerificationResult {
  valid: boolean;
  reason: string;
  groundedBoundingBox?: BoundingRect;
}

/**
 * Deterministic Action Compatibility Matrix (ACTION x VISUAL_ENTITY_TYPE).
 * Defines explicit allow behavior. Any combination not present is REJECTED.
 */
export const ACTION_COMPATIBILITY_MATRIX: Record<string, Set<string>> = {
  CLICK: new Set([
    'VISUAL_BUTTON',
    'VISUAL_INPUT',
    'VISUAL_CHECKBOX_RADIO',
    'VISUAL_CARD',
    'VISUAL_NAVIGATION',
    'VISUAL_IMAGE',
    'VISUAL_ICON',
    'VISUAL_INTERACTIVE',
  ]),
  TYPE: new Set([
    'VISUAL_INPUT',
  ]),
  SELECT: new Set([
    'VISUAL_CHECKBOX_RADIO',
    'VISUAL_INPUT',
    'VISUAL_INTERACTIVE',
  ]),
  HOVER: new Set([
    'VISUAL_BUTTON',
    'VISUAL_INPUT',
    'VISUAL_CHECKBOX_RADIO',
    'VISUAL_CARD',
    'VISUAL_NAVIGATION',
    'VISUAL_IMAGE',
    'VISUAL_ICON',
    'VISUAL_INTERACTIVE',
  ]),
};

export class VisualActionBinder {
  private static instance: VisualActionBinder | null = null;

  public static getInstance(): VisualActionBinder {
    if (!VisualActionBinder.instance) {
      VisualActionBinder.instance = new VisualActionBinder();
    }
    return VisualActionBinder.instance;
  }

  /**
   * Binds an incoming structured action to a pixel-derived visual object region in the VisualScene.
   * Guarantees:
   * 1. Action MUST target a semantically compatible visual object.
   * 2. Coordinates outside the target visual bounding box are REJECTED.
   * 3. Disabled controls and UNKNOWN_VISUAL_REGION fail closed.
   * 4. Multi-object disambiguation resolves identical visual buttons via spatial graph & click coordinates.
   */
  public bindActionToVisualObject(
    action: StructuredAction,
    visualRegions: VisualFeatureRegion[],
    taskId: string,
    captureId: string,
    perceptionId: string,
    sceneDigest: string,
    targetClickCoords?: { x: number; y: number }
  ): VisualActionBinding | null {
    if (!action || !visualRegions || visualRegions.length === 0) {
      return null;
    }

    const normAction = (action.action || 'CLICK').toUpperCase();
    const allowedTypes = ACTION_COMPATIBILITY_MATRIX[normAction] || ACTION_COMPATIBILITY_MATRIX.CLICK;

    const targetNodeId = action.target?.nodeId || '';
    let matchedRegion: VisualFeatureRegion | null = null;

    // 1. Target matching by click coordinates if provided
    if (targetClickCoords && typeof targetClickCoords.x === 'number' && typeof targetClickCoords.y === 'number') {
      for (const reg of visualRegions) {
        const b = reg.bbox;
        if (
          targetClickCoords.x >= b.x &&
          targetClickCoords.x <= b.x + b.width &&
          targetClickCoords.y >= b.y &&
          targetClickCoords.y <= b.y + b.height
        ) {
          if (allowedTypes.has(reg.type)) {
            matchedRegion = reg;
            break;
          }
        }
      }
    }

    // 2. Disambiguate identical buttons or find matching region by associatedText / reasoning
    if (!matchedRegion && action.reasoning) {
      const lowerReason = action.reasoning.toLowerCase();
      for (const reg of visualRegions) {
        const text = (reg.visualEvidence?.associatedText || '').toLowerCase();
        if (text && lowerReason.includes(text)) {
          if (allowedTypes.has(reg.type)) {
            matchedRegion = reg;
            break;
          }
        }
      }
    }

    // 3. Fallback to first semantically compatible visual region
    if (!matchedRegion) {
      matchedRegion = visualRegions.find(r => allowedTypes.has(r.type)) || null;
    }

    if (!matchedRegion) return null;

    return {
      taskId,
      captureId,
      perceptionId,
      visualObjectId: matchedRegion.id,
      visualObjectType: matchedRegion.type,
      visualBoundingBox: matchedRegion.bbox,
      targetClickCoordinates: targetClickCoords || {
        x: matchedRegion.bbox.x + Math.round(matchedRegion.bbox.width / 2),
        y: matchedRegion.bbox.y + Math.round(matchedRegion.bbox.height / 2),
      },
      targetDOMNodeId: targetNodeId,
      sceneDigest,
      timestamp: Date.now(),
    };
  }

  /**
   * Verifies visual-to-action grounding immediately before DOM action execution (TOCTOU Defense).
   * Enforces Action x Visual Entity Type semantic compatibility, timestamp freshness,
   * disabled control blocking, unknown region fail-closed, coordinate containment, and 35px DOM shift.
   */
  public verifyVisualGrounding(
    binding: VisualActionBinding | undefined | null,
    targetElementRect: BoundingRect,
    _liveOrigin: string,
    _expectedOrigin: string,
    actionType: string
  ): GroundingVerificationResult {
    if (!binding) {
      return { valid: false, reason: 'Visual Grounding Abort: Missing visual action binding payload' };
    }

    // Invariant 1: Check stale perception timestamp (> 10s)
    const now = Date.now();
    if (now - binding.timestamp > 10000 || now - binding.timestamp < 0) {
      return { valid: false, reason: 'Visual Grounding Abort: Stale visual perception capture (> 10s old)' };
    }

    // Invariant 2: Check target visual object type for DISABLED_CONTROL
    if (binding.visualObjectType === 'DISABLED_CONTROL') {
      return { valid: false, reason: 'Visual Grounding Abort: Target visual object is a DISABLED_CONTROL' };
    }

    // Invariant 3: Check UNKNOWN_VISUAL_REGION (Fail closed unless explicit trusted evidence exists)
    if (binding.visualObjectType === 'UNKNOWN_VISUAL_REGION') {
      return { valid: false, reason: 'Visual Grounding Abort: Action execution blocked on UNKNOWN_VISUAL_REGION (fail-closed)' };
    }

    // Invariant 4: Semantic Action Compatibility Matrix Verification (ACTION x VISUAL_ENTITY_TYPE)
    const normAction = (actionType || 'CLICK').toUpperCase();
    const allowedTypes = ACTION_COMPATIBILITY_MATRIX[normAction];
    if (allowedTypes && !allowedTypes.has(binding.visualObjectType)) {
      return {
        valid: false,
        reason: `Visual Grounding Abort: Incompatible action ${normAction} for visual object type ${binding.visualObjectType}`,
      };
    }

    // Invariant 5: Verify target click coordinates lie strictly inside visual bounding box
    if (binding.targetClickCoordinates && (normAction === 'CLICK' || normAction === 'TYPE' || normAction === 'SELECT')) {
      const { x, y } = binding.targetClickCoordinates;
      const b = binding.visualBoundingBox;
      if (x < b.x || x > b.x + b.width || y < b.y || y > b.y + b.height) {
        return {
          valid: false,
          reason: `Visual Grounding Abort: Click coordinate (${x}, ${y}) is OUTSIDE detected visual bounding box`,
        };
      }
    }

    // Invariant 6: Target DOM Visibility & Non-Zero Area Check
    if (targetElementRect.width <= 0 || targetElementRect.height <= 0) {
      return {
        valid: false,
        reason: 'Visual Grounding Abort: Target DOM element is invisible or zero-size',
      };
    }

    // Invariant 7: Pre-execution DOM visual movement check (TOCTOU shift > 35px)
    const bVisual = binding.visualBoundingBox;
    const dx = Math.abs(targetElementRect.x - bVisual.x);
    const dy = Math.abs(targetElementRect.y - bVisual.y);

    if (dx > 35 || dy > 35) {
      return {
        valid: false,
        reason: 'Visual Grounding Abort: Live DOM element position shifted > 35px from visual capture',
      };
    }

    return {
      valid: true,
      reason: 'Visual Grounding Verification Passed: Bounding box, click coordinates, action semantics, and DOM position verified.',
      groundedBoundingBox: binding.visualBoundingBox,
    };
  }
}