export type ActionType =
  | 'CLICK'
  | 'TYPE'
  | 'SELECT'
  | 'SCROLL'
  | 'NAVIGATE'
  | 'HOVER'
  | 'WAIT';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface StructuredAction {
  actionId: string;
  taskId: string;
  action: ActionType;
  target: {
    nodeId?: string;
    selector?: string;
    xpath?: string;
  };
  value?: string; // May contain token like "PERSON#A72F" or literal input
  confidence: number;
  reasoning: string;
}

export interface IntentAnchor {
  taskId: string;
  userPrompt: string;
  targetGoal: string; // e.g. "flight_booking"
  originDomain: string;
  allowedActions: ActionType[];
  allowedSlots: Record<string, string>; // Slot type -> expected slot role
  allowedDataClasses: string[];
  forbiddenDataClasses: string[];
  allowedNavigationDomains: string[];
  permittedActionTypes: ActionType[];
  maxExecutionSteps: number;
  currentStep: number;
  createdAt: number;
  immutableHash: string;
  chainHistory: StructuredAction[];
}

export interface LocalSemanticAnalysisResult {
  semanticScore: number; // 0.0 (Malicious/Divergent) to 1.0 (Aligned)
  matchedConstraint?: string;
  isSemanticViolation: boolean;
  violationReason?: string;
  actionChainRisk: RiskLevel;
  analysisLatencyMs: number;
}

export interface ActionFirewallResult {
  actionId: string;
  decision: 'ALLOW' | 'CONFIRM' | 'BLOCK';
  riskLevel: RiskLevel;
  reason: string;
  untrustedInstructionDetected: boolean;
  intentMismatch: boolean;
  targetExists: boolean;
  originValid: boolean;
  semanticAnalysis: LocalSemanticAnalysisResult;
  resolvedValue?: string; // Tokens un-vaulted to real local values ONLY if decision is ALLOW/CONFIRM
}
