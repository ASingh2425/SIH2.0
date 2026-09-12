export type SensitivityTier = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type TaskNecessity = 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';

export type PrivacyTreatment =
  | 'KEEP'
  | 'ABSTRACT'
  | 'TOKENIZE'
  | 'MASK'
  | 'LOCAL_ONLY'
  | 'REMOVE';

export type VisualPrivacyState =
  | 'VERIFIED_SAFE'
  | 'PII_DETECTED'
  | 'VISUAL_PRIVACY_UNVERIFIED';

export type EntityType =
  | 'EMAIL'
  | 'PHONE'
  | 'CREDIT_CARD'
  | 'PASSWORD'
  | 'NAME'
  | 'GOVT_ID'
  | 'ADDRESS'
  | 'UPI_ID'
  | 'DOB'
  | 'AUTH_CODE'
  | 'UNKNOWN_SENSITIVE'
  | 'UNVERIFIED_VISUAL_REGION';

export type DetectionSource =
  | 'REGEX'
  | 'DOM_ATTR'
  | 'ARIA'
  | 'VISUAL_OCR'
  | 'CANVAS_TEXT'
  | 'SVG_TEXT'
  | 'IMAGE_TEXT'
  | 'MODEL_NER';

export type MLInferenceBackend = 'webgpu' | 'wasm' | 'cpu_fallback';

export interface MLBackendStatus {
  backend: MLInferenceBackend;
  modelName: string;
  inferenceLatencyMs: number;
  isFallback: boolean;
  gpuDeviceName?: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DetectedEntity {
  id: string;
  type: EntityType;
  rawValue: string;
  maskedDisplay: string;
  confidence: number;
  sensitivity: SensitivityTier;
  taskNecessity: TaskNecessity;
  treatment: PrivacyTreatment;
  assignedToken?: string;
  nodeId?: string;
  boundingRect?: BoundingBox;
  detectionSource: DetectionSource;
  isVisualOnly?: boolean;
}

export interface PrivacyPolicyConfig {
  confidenceThreshold: number;
  failClosedTreatment: 'REMOVE' | 'MASK' | 'LOCAL_ONLY';
  enableVisualObfuscation: boolean;
  sensitivityWeights: Record<SensitivityTier, number>;
}

export const DEFAULT_PRIVACY_CONFIG: PrivacyPolicyConfig = {
  confidenceThreshold: 0.80,
  failClosedTreatment: 'REMOVE',
  enableVisualObfuscation: true,
  sensitivityWeights: {
    CRITICAL: 1.0,
    HIGH: 0.8,
    MEDIUM: 0.5,
    LOW: 0.2,
  },
};
