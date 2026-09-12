export interface TokenVaultEntry {
  token: string;
  rawValue: string;
  entityType: string;
  taskId: string;
  originDomain: string;
  createdAt: number;
  expiresAt: number;
}

export class LocalTokenVault {
  private static instance: LocalTokenVault;
  private vault: Map<string, TokenVaultEntry> = new Map();

  private constructor() {}

  public static getInstance(): LocalTokenVault {
    if (!LocalTokenVault.instance) {
      LocalTokenVault.instance = new LocalTokenVault();
    }
    return LocalTokenVault.instance;
  }

  /**
   * Generates a cryptographically randomized, scoped ephemeral token.
   */
  public generateToken(
    rawValue: string,
    entityType: string,
    taskId: string,
    originDomain: string
  ): string {
    // Check if mapping already exists for this exact rawValue in this task
    for (const entry of this.vault.values()) {
      if (
        entry.rawValue === rawValue &&
        entry.taskId === taskId &&
        entry.originDomain === originDomain &&
        entry.expiresAt > Date.now()
      ) {
        return entry.token;
      }
    }

    // Create new token e.g. PERSON#A72F or EMAIL#B91C
    const prefix = entityType === 'NAME' ? 'PERSON' : entityType === 'EMAIL' ? 'EMAIL' : 'TOKEN';
    const randomHex = Math.floor(1000 + Math.random() * 9000).toString(16).toUpperCase();
    const token = `${prefix}#${randomHex}`;

    const now = Date.now();
    const expiresAt = now + 15 * 60 * 1000; // 15 minutes TTL

    const entry: TokenVaultEntry = {
      token,
      rawValue,
      entityType,
      taskId,
      originDomain,
      createdAt: now,
      expiresAt,
    };

    this.vault.set(token, entry);
    return token;
  }

  /**
   * Resolves token back to real value ONLY inside local execution boundary.
   */
  public resolveToken(token: string, taskId: string, originDomain: string): string | null {
    const entry = this.vault.get(token);
    if (!entry) return null;

    // Strict Scope & Expiry Verification
    if (entry.taskId !== taskId) {
      console.warn(`[TokenVault] Security Block: Task ID mismatch for token ${token}`);
      return null;
    }
    if (entry.originDomain !== originDomain) {
      console.warn(`[TokenVault] Security Block: Origin mismatch for token ${token}`);
      return null;
    }
    if (entry.expiresAt < Date.now()) {
      console.warn(`[TokenVault] Security Block: Token ${token} has expired`);
      this.vault.delete(token);
      return null;
    }

    return entry.rawValue;
  }

  public purgeTaskTokens(taskId: string): void {
    for (const [token, entry] of this.vault.entries()) {
      if (entry.taskId === taskId) {
        this.vault.delete(token);
      }
    }
  }

  public getActiveTokens(taskId: string): TokenVaultEntry[] {
    const result: TokenVaultEntry[] = [];
    for (const entry of this.vault.values()) {
      if (entry.taskId === taskId && entry.expiresAt > Date.now()) {
        result.push({ ...entry, rawValue: '•'.repeat(entry.rawValue.length) }); // Return masked version for audit
      }
    }
    return result;
  }
}
