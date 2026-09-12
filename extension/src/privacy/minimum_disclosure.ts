import {
  DEFAULT_PRIVACY_CONFIG,
  DetectedEntity,
  PrivacyPolicyConfig,
  PrivacyTreatment,
  SensitivityTier,
  TaskNecessity,
} from '../types/privacy';
import { IntentAnchor } from '../types/action';
import { LocalTokenVault } from './token_vault';

export class MinimumDisclosureEngine {
  private config: PrivacyPolicyConfig;
  private tokenVault: LocalTokenVault;

  constructor(config: PrivacyPolicyConfig = DEFAULT_PRIVACY_CONFIG) {
    this.config = config;
    this.tokenVault = LocalTokenVault.getInstance();
  }

  /**
   * Applies Task-Aware Minimum Disclosure Matrix to every detected entity.
   */
  public evaluateDisclosure(
    entities: DetectedEntity[],
    intentAnchor: IntentAnchor
  ): DetectedEntity[] {
    const evaluated: DetectedEntity[] = [];

    for (const ent of entities) {
      // 1. Determine Task Necessity based on Intent Anchor slots & prompt
      const necessity = this.determineTaskNecessity(ent, intentAnchor);
      ent.taskNecessity = necessity;

      // 2. Fail-Closed Check: Low confidence entities automatically get REMOVE/MASK
      if (ent.confidence < this.config.confidenceThreshold) {
        ent.treatment = this.config.failClosedTreatment;
        evaluated.push(ent);
        continue;
      }

      // 3. Matrix Decision based on Sensitivity Tier x Task Necessity
      const treatment = this.computeMatrixTreatment(ent.sensitivity, necessity);
      ent.treatment = treatment;

      // 4. Token Vault Assignment if treatment is TOKENIZE
      if (treatment === 'TOKENIZE') {
        const token = this.tokenVault.generateToken(
          ent.rawValue,
          ent.type,
          intentAnchor.taskId,
          intentAnchor.originDomain
        );
        ent.assignedToken = token;
      }

      evaluated.push(ent);
    }

    return evaluated;
  }

  private determineTaskNecessity(ent: DetectedEntity, intentAnchor: IntentAnchor): TaskNecessity {
    const lowerPrompt = intentAnchor.userPrompt.toLowerCase();
    const val = ent.rawValue.toLowerCase();

    // Critical credentials (passwords, CVV, PINs) are NEVER task necessary for cloud reasoning
    if (ent.sensitivity === 'CRITICAL' || ent.type === 'PASSWORD') {
      return 'NONE';
    }

    // Name & Email for passenger/user booking are HIGH necessity
    if (
      (ent.type === 'NAME' || ent.type === 'EMAIL') &&
      (intentAnchor.targetGoal === 'flight_booking' || intentAnchor.targetGoal === 'ecommerce_checkout')
    ) {
      return 'HIGH';
    }

    // Check if value is explicitly referenced in user prompt (e.g. "Delhi")
    if (val.length > 2 && lowerPrompt.includes(val)) {
      return 'HIGH';
    }

    // Phone numbers
    if (ent.type === 'PHONE') {
      return 'MEDIUM';
    }

    return 'NONE';
  }

  private computeMatrixTreatment(
    sensitivity: SensitivityTier,
    necessity: TaskNecessity
  ): PrivacyTreatment {
    if (sensitivity === 'CRITICAL') {
      return necessity === 'HIGH' ? 'LOCAL_ONLY' : 'REMOVE';
    }

    if (sensitivity === 'HIGH') {
      if (necessity === 'HIGH') return 'TOKENIZE';
      if (necessity === 'MEDIUM') return 'TOKENIZE';
      return 'REMOVE';
    }

    if (sensitivity === 'MEDIUM') {
      if (necessity === 'HIGH') return 'TOKENIZE';
      if (necessity === 'MEDIUM') return 'ABSTRACT';
      return 'MASK';
    }

    // LOW Sensitivity
    if (necessity === 'HIGH' || necessity === 'MEDIUM') return 'KEEP';
    return 'MASK';
  }
}
