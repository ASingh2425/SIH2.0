import { ActionType, IntentAnchor } from '../types/action';

export class TaskIntentParser {
  /**
   * Parses user task prompt and constructs an immutable IntentAnchor with structured security constraints.
   */
  public createIntentAnchor(
    taskId: string,
    userPrompt: string,
    originDomain: string
  ): IntentAnchor {
    const lowerPrompt = userPrompt.toLowerCase();

    let targetGoal = 'generic_web_navigation';
    const allowedSlots: Record<string, string> = {};
    const allowedDataClasses: string[] = [];
    const forbiddenDataClasses: string[] = [
      'password',
      'credit_card',
      'cvv',
      'passport',
      'bank_account',
      'exfiltrate',
      'delete_account',
    ];

    // Flight Booking Intent Identification
    if (
      lowerPrompt.includes('flight') ||
      lowerPrompt.includes('book') ||
      lowerPrompt.includes('ticket') ||
      lowerPrompt.includes('airline')
    ) {
      targetGoal = 'flight_booking';

      const fromMatch = userPrompt.match(/from\s+([A-Za-z]+)/i);
      const toMatch = userPrompt.match(/to\s+([A-Za-z]+)/i);

      if (fromMatch) allowedSlots['origin_city'] = fromMatch[1];
      if (toMatch) allowedSlots['destination_city'] = toMatch[1];
      allowedSlots['passenger_name'] = 'TOKENIZED_SLOT';
      allowedSlots['passenger_email'] = 'TOKENIZED_SLOT';

      allowedDataClasses.push('origin_city', 'destination_city', 'passenger_name', 'passenger_email');
    } else if (lowerPrompt.includes('buy') || lowerPrompt.includes('checkout') || lowerPrompt.includes('shop')) {
      targetGoal = 'ecommerce_checkout';
      allowedSlots['shipping_address'] = 'TOKENIZED_SLOT';
      allowedDataClasses.push('shipping_address', 'item_quantity');
    }

    const permittedActionTypes: ActionType[] = [
      'CLICK',
      'TYPE',
      'SELECT',
      'SCROLL',
      'NAVIGATE',
      'HOVER',
      'WAIT',
    ];

    const createdAt = Date.now();
    const immutableString = `${taskId}:${targetGoal}:${originDomain}:${createdAt}`;
    const immutableHash = this.simpleHash(immutableString);

    return {
      taskId,
      userPrompt,
      targetGoal,
      originDomain,
      allowedActions: permittedActionTypes,
      allowedSlots,
      allowedDataClasses,
      forbiddenDataClasses,
      allowedNavigationDomains: [originDomain],
      permittedActionTypes,
      maxExecutionSteps: 12,
      currentStep: 0,
      createdAt,
      immutableHash,
      chainHistory: [],
    };
  }

  private simpleHash(input: string): string {
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash |= 0;
    }
    return 'anchor_' + Math.abs(hash).toString(16);
  }
}
