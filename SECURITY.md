# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 5.4.x   | ✅ Active |
| 5.3.x   | ✅ Critical fixes |
| < 5.3   | ❌ End of life |

## Audit Status

### v5.4.1 (2026-05-21) — Kimi Code CLI Audit

Third-party independent security audit covering all source files. **18 CRITICAL** issues found and resolved:

| Category | Found | Fixed |
|----------|-------|-------|
| Auth bypass (reverse proxy) | 1 | ✅ `HMAC` token gate |
| Prompt injection guard fail-open | 1 | ✅ fail-closed |
| API key exposure | 1 | ✅ `.env.dontredact` removed |
| Shell injection | 4 | ✅ `safe_subprocess_run` hardened |
| Code injection (Python/MATLAB) | 3 | ✅ allow-lists + sandbox |
| MCP broken methods | 2 | ✅ corrected API calls |
| Subprocess/async misuse | 2 | ✅ fixed |
| Path traversal | 1 | ✅ `is_relative_to()` guard |
| C4 mathematical inconsistency | 1 | ✅ unified definitions |
| Missing LLM provider factories | 1 | ✅ 4 providers added |
| Agent message history loss | 1 | ✅ full conversation |
| **Total CRITICAL** | **18** | **✅ ALL FIXED** |
| HIGH | 16 | ✅ ALL FIXED |
| MEDIUM | 36 | ✅ ALL FIXED |

**No remaining CRITICAL or HIGH findings. 1,063 tests pass with 0 failures.**

### v5.4.0 (2026-05-18) — Internal Audit

v5.4.0 passed a full security audit covering 1,038 source files:

| Check | Result |
|-------|--------|
| `shell=True` subprocess | 0 found |
| SQL injection | 0 — all 140+ use `?` parameters |
| Credential leaks | 0 hardcoded keys |
| `eval()` / `exec()` | 1 (calculator — sandboxed + AST-validated) |
| `pickle` / unsafe YAML | 0 — only `yaml.safe_load` |
| MD5 usage | 0 — all 15 replaced with SHA-256 |
| Subprocess wrappers | All wrapped in try/except |

## Reporting Vulnerabilities

**Please do NOT open public issues for security bugs.**

Instead, email: security@turbo-cdi.dev (or open a private security advisory on GitHub)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work on a fix.

## Security Measures

- JWT with HS256, 24h expiry
- bcrypt password hashing
- Rate limiting (IP + WebSocket sliding window)
- Input validation via Pydantic v2
- Parameterized SQL queries
- Non-root Docker containers
- Security scanning in CI (trivy, pip-audit, npm audit, bandit)
- Content Security Policy (CSP) without unsafe-inline
- CORS with strict allowlist
- HSTS in production
- API key validation
- Structured audit logging with hash-chain integrity
- HSM key management stub (production: AWS CloudHSM / Thales Luna)
- Automated penetration testing

## Bug Bounty Program

### Scope

The TURBO-CDI bug bounty program covers the following assets:

| Asset | Type | In Scope |
|-------|------|----------|
| `src/api/` | Backend API | ✅ Yes |
| `src/api/auth.py` | Authentication | ✅ Yes |
| `src/api/middleware/security.py` | Security middleware | ✅ Yes |
| `src/security/` | Security modules | ✅ Yes |
| `landing/` + TUI v9 | Terminal + static site (primary UI) | ✅ Yes |
| `docker/` | Container configs | ✅ Yes |
| `k8s/` | Kubernetes manifests | ✅ Yes |
| Third-party dependencies | Out of scope | ❌ No |
| Denial of Service (DoS) | Out of scope | ❌ No |

### Rewards

| Severity | CVSS Score | Reward Range |
|----------|-----------|--------------|
| Critical | 9.0 - 10.0 | $2,000 - $5,000 |
| High | 7.0 - 8.9 | $500 - $1,500 |
| Medium | 4.0 - 6.9 | $100 - $400 |
| Low | 0.1 - 3.9 | $50 - $100 |
| Informational | 0.0 | Swag / Hall of Fame |

### Rules

1. **Do NOT** test on production systems without explicit permission.
2. **Do NOT** access, modify, or delete data belonging to other users.
3. **Do NOT** perform DoS attacks, social engineering, or physical attacks.
4. **Do NOT** publicly disclose vulnerabilities before a fix is deployed.
5. Provide a clear proof of concept with steps to reproduce.
6. Allow up to 90 days for remediation before public disclosure.

### Submission Process

1. Send report to security@turbo-cdi.dev with subject: `[Bug Bounty] <title>`
2. Include: vulnerability type, affected endpoint, reproduction steps, impact assessment, suggested fix
3. We acknowledge receipt within 48 hours
4. We triage within 7 days and assign severity
5. We fix within 30 days for Critical/High, 60 days for Medium/Low
6. Reward is paid within 14 days of fix deployment

### Hall of Fame

We publicly acknowledge researchers who responsibly disclose valid vulnerabilities (with their permission).

## Acknowledgments

We credit security researchers who responsibly disclose vulnerabilities.
