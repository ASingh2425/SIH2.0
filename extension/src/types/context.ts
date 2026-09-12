import { MLBackendStatus, PrivacyTreatment } from './privacy';

export interface BoundingRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DOMNodeDescriptor {
  nodeId: string;
  tagName: string;
  role?: string;
  text?: string;
  placeholder?: string;
  inputType?: string;
  nameAttr?: string;
  idAttr?: string;
  attributes: Record<string, string>;
  bounds: BoundingRect;
  isInput: boolean;
  isClickable: boolean;
  isVisible: boolean;
  sanitizedValue?: string;
  appliedTreatment?: PrivacyTreatment;
  assignedToken?: string;
}

export interface PrivacyBoundaryReport {
  timestamp: number;
  rawEntitiesDetected: number;
  entitiesTransmitted: number;
  entitiesBlocked: number;
  entitiesTokenized: number;
  localOnlyEntities: number;
  sanitizedPayloadSizeBytes: number;
  rawPayloadSizeBytes: number;
  zeroRawPIIVerified: boolean;
  visualRedactionVerified: boolean;
  visualPrivacyState: 'VERIFIED_SAFE' | 'PII_DETECTED' | 'VISUAL_PRIVACY_UNVERIFIED';
  unverifiedVisualRegionsMasked: number;
  validatorVersion: string;
  validationDetails: string[];
}

export interface SanitizedContextPayload {
  taskId: string;
  timestamp: number;
  originDomain: string;
  viewport: { width: number; height: number };
  sanitizedDomNodes: DOMNodeDescriptor[];
  sanitizedScreenshotBase64?: string; // Client-redacted canvas base64 image
  mlBackendStatus: MLBackendStatus;
  boundaryReport: PrivacyBoundaryReport;
}
