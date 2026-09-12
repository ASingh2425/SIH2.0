import { EntityType, MLBackendStatus, PrivacyTreatment, SensitivityTier, TaskNecessity } from './privacy';
import { ActionType, RiskLevel } from './action';
import { PrivacyBoundaryReport } from './context';

export interface PrivacyLedgerEntry {
  entryId: string;
  timestamp: number;
  taskId: string;
  entityType: EntityType;
  maskedDisplay: string;
  confidence: number;
  sensitivity: SensitivityTier;
  taskNecessity: TaskNecessity;
  treatment: PrivacyTreatment;
  crossedNetwork: boolean; // GUARANTEED FALSE for raw sensitive values
  assignedToken?: string;
  isVisualOnly?: boolean;
}

export interface ActionAuditRecord {
  recordId: string;
  timestamp: number;
  taskId: string;
  proposedAction: ActionType;
  targetNodeId?: string;
  riskLevel: RiskLevel;
  firewallDecision: 'ALLOW' | 'CONFIRM' | 'BLOCK';
  reason: string;
  untrustedContentFlag: boolean;
  semanticViolationFlag: boolean;
  executedSuccessfully?: boolean;
}

export interface SystemPerformanceMetrics {
  domContextExtractionAccuracyPct: number;
  visualPerceptionAccuracyPct: number;
  piiPrecisionPct: number;
  piiRecallPct: number;
  redactionPrecisionPct: number;
  perceptionLatencyMs: number;
  ocrLatencyMs: number;
  mdeLatencyMs: number;
  semanticGuardLatencyMs: number;
  firewallLatencyMs: number;
  networkLatencyMs: number;
  remoteVlmLatencyMs: number;
  totalE2ELatencyMs: number;
  cpuUsagePercentage: number;
  ramUsageMB: number;
  gpuUsagePercentage?: number;
  minimumDisclosureScore: number;
  privacyUtilityEfficiency: number;
  unsafeActionExecutionRatePct: number;
  attackDetectionRecallPct: number;
  falsePositiveRatePct: number;
  mlBackendStatus: MLBackendStatus;
  fastPathUsed: boolean;
}

export interface CompleteAuditLedger {
  taskId: string;
  privacyEntries: PrivacyLedgerEntry[];
  actionRecords: ActionAuditRecord[];
  boundaryReports: PrivacyBoundaryReport[];
  metrics: SystemPerformanceMetrics;
}
