import { BoundingRect } from '../types/context';

export type UIElementClass =
  | 'BUTTON'
  | 'INPUT'
  | 'CHECKBOX'
  | 'RADIO'
  | 'DROPDOWN'
  | 'TAB'
  | 'NAVIGATION'
  | 'CARD'
  | 'DIALOG'
  | 'TABLE'
  | 'IMAGE'
  | 'ICON'
  | 'TEXT'
  | 'FORM'
  | 'CONTAINER'
  | 'UNKNOWN';

export interface VisualEvidenceMetrics {
  edgeDensity: number;
  textDensity: number;
  contrastScore: number;
  luminanceAvg: number;
  pixelVariance: number;
  isHighContrast: boolean;
  isRectangularBorder: boolean;
  aspectRatio: number;
  borderContinuity?: number;
  fillUniformity?: number;
}

export interface PerceptionObject {
  id: string;
  type: UIElementClass;
  bbox: BoundingRect;
  confidence: number;
  source: 'onnx_object_detector' | 'ocr_fusion' | 'pixel_heuristic_fallback' | 'dom_semantic_hint' | 'fallback' | 'unknown';
  associatedText?: string;
  visualEvidence?: VisualEvidenceMetrics;
  uncertaintyState: 'CONFIDENT' | 'AMBIGUOUS' | 'UNCERTAIN_FALLBACK';
}

export interface PerceptionRelationship {
  sourceId: string;
  sourceType: UIElementClass;
  relationship: 'ABOVE' | 'BELOW' | 'LEFT_OF' | 'RIGHT_OF' | 'INSIDE' | 'CONTAINS';
  targetId: string;
  targetType: UIElementClass;
}

export interface VisualPerceptionPrediction {
  timestamp: number;
  objects: PerceptionObject[];
  relationships: PerceptionRelationship[];
  modelId: string;
  backendUsed: 'onnx_wasm' | 'onnx_webgpu' | 'onnx_cpu' | 'pixel_heuristic' | 'fallback';
  inferenceLatencyMs: number;
  viewport: { width: number; height: number };
  rawTensorShape?: number[];
  uncertaintyRatio: number;
}

export interface VisualModelInfo {
  modelId: string;
  modelName: string;
  version: string;
  supportedClasses: UIElementClass[];
  inputTensorShape: number[];
  modelSizeBytes: number;
}

export interface VisualBackendInfo {
  backend: 'onnx_wasm' | 'onnx_webgpu' | 'onnx_cpu' | 'pixel_heuristic' | 'fallback';
  isHardwareAccelerated: boolean;
  isFallback: boolean;
  deviceInfo?: string;
}

export interface VisualPerceptionModel {
  initialize(): Promise<boolean>;
  predict(
    imageData: ImageData | HTMLCanvasElement,
    viewportWidth?: number,
    viewportHeight?: number
  ): Promise<VisualPerceptionPrediction>;
  getModelInfo(): VisualModelInfo;
  getBackendInfo(): VisualBackendInfo;
}
