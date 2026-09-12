import { FirewallAuthorizationToken, StructuredAction } from '../types/action';
import { LocalTokenVault } from '../privacy/token_vault';
import { LocalActionFirewall } from '../firewall/action_firewall';

export class BrowserExecutor {
  private tokenVault = LocalTokenVault.getInstance();

  /**
   * Executes verified action in browser DOM ONLY after firewall authorization token validation
   * AND immediate pre-execution DOM re-evaluation (TOCTOU defense).
   */
  public async executeVerifiedAction(
    action: StructuredAction,
    nodeMap: Map<string, HTMLElement>,
    originDomain: string,
    authorizationToken: FirewallAuthorizationToken,
    firewall: LocalActionFirewall
  ): Promise<{ success: boolean; message: string }> {
    // 0. Firewall Authorization Gate Verification
    if (!authorizationToken) {
      return { success: false, message: 'Execution Security Abort: Missing Firewall Authorization Token' };
    }

    if (!firewall) {
      return { success: false, message: 'Execution Security Abort: Missing LocalActionFirewall verifier instance' };
    }

    const authVerification = firewall.verifyAuthorizationToken(authorizationToken, action, originDomain);
    if (!authVerification.valid) {
      return {
        success: false,
        message: `Execution Security Abort: Firewall Authorization Failed (${authVerification.reason})`,
      };
    }

    const targetNodeId = action.target.nodeId;
    if (!targetNodeId) {
      return { success: false, message: 'Action execution failed: Missing target nodeId' };
    }

    // 1. Immediate Pre-Execution DOM & Origin Verification (TOCTOU Defense)
    const currentOrigin = window.location.origin;
    if (!firewall.strictOriginMatch(currentOrigin, originDomain)) {
      return {
        success: false,
        message: `Pre-Execution Security Abort: Active window origin (${currentOrigin}) mutated from task origin (${originDomain})`,
      };
    }

    const targetEl = nodeMap.get(targetNodeId) || document.getElementById(targetNodeId);
    if (!targetEl || !document.body.contains(targetEl)) {
      return { success: false, message: `Pre-Execution Security Abort: Target element ${targetNodeId} not found or mutated in live DOM` };
    }

    // Target Attribute Immutability & Mutation Verification
    const idAttr = (targetEl.getAttribute('id') || '').toLowerCase();
    const typeAttr = (targetEl.getAttribute('type') || '').toLowerCase();
    const actionAttr = (targetEl.getAttribute('data-action') || '').toLowerCase();

    if (
      idAttr.includes('transfer') ||
      idAttr.includes('delete') ||
      idAttr.includes('reset') ||
      actionAttr.includes('exfiltrate') ||
      (typeAttr === 'password' && action.action !== 'TYPE')
    ) {
      return {
        success: false,
        message: `Pre-Execution Security Abort: Target element attributes mutated into security-sensitive target ('${idAttr}') post-approval`,
      };
    }

    // Check for clickjacking overlay or hidden target
    const rect = targetEl.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0 && action.action !== 'WAIT') {
      return { success: false, message: `Pre-Execution Security Abort: Target element ${targetNodeId} is hidden or invisible` };
    }

    try {
      switch (action.action) {
        case 'CLICK':
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
          targetEl.click();
          targetEl.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
          return { success: true, message: `Successfully clicked target ${targetNodeId}` };

        case 'TYPE': {
          let valueToInsert = action.value || '';

          // Check if value contains an ephemeral local token (e.g. PERSON#A72F)
          if (valueToInsert.includes('#')) {
            const tokenMatch = valueToInsert.match(/([A-Z]+#[A-F0-9]+)/);
            if (tokenMatch) {
              const token = tokenMatch[1];
              const resolvedRealValue = this.tokenVault.resolveToken(
                token,
                action.taskId,
                originDomain
              );
              if (resolvedRealValue) {
                valueToInsert = valueToInsert.replace(token, resolvedRealValue);
              } else {
                return {
                  success: false,
                  message: `Token un-vaulting failed: Security block or expired token ${token}`,
                };
              }
            }
          }

          targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
          targetEl.focus();

          if (targetEl instanceof HTMLInputElement || targetEl instanceof HTMLTextAreaElement) {
            targetEl.value = valueToInsert;
            targetEl.dispatchEvent(new Event('input', { bubbles: true }));
            targetEl.dispatchEvent(new Event('change', { bubbles: true }));
          } else {
            targetEl.innerText = valueToInsert;
          }

          return {
            success: true,
            message: `Successfully typed into target ${targetNodeId} (Tokens un-vaulted locally)`,
          };
        }

        case 'SCROLL':
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
          return { success: true, message: `Scrolled element ${targetNodeId} into view` };

        case 'WAIT':
          await new Promise(r => setTimeout(r, 1000));
          return { success: true, message: 'Waited 1000ms' };

        default:
          return { success: false, message: `Unsupported action type: ${action.action}` };
      }
    } catch (err: any) {
      return { success: false, message: `DOM Execution exception: ${err.message}` };
    }
  }
}
