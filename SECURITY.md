# Security Policy

## Overview

Compliance OS handles sensitive financial and compliance data for Global Capability Centers (GCCs) in India. Security is paramount to our mission. This document outlines our security policies and procedures for reporting vulnerabilities.

**Core Principle**: "If it cannot stand up to an auditor, it does not ship."

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 0.1.x   | :white_check_mark: | Current development version (Phase 1 complete) |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow responsible disclosure practices:

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email security concerns to: [security@compliance-os.com] (Replace with actual email)
3. Include the following information:
   - Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
   - Full paths of affected source files
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the vulnerability
   - Suggested remediation (if any)

### Response Timeline

- **Initial Response**: Within 48 hours of report submission
- **Vulnerability Assessment**: Within 1 week
- **Fix Timeline**:
  - Critical vulnerabilities: 1-7 days
  - High severity: 1-2 weeks
  - Medium severity: 2-4 weeks
  - Low severity: Next planned release

### What to Expect

1. **Acknowledgment**: We'll confirm receipt of your report within 48 hours
2. **Assessment**: We'll investigate and assess the severity and impact
3. **Fix Development**: We'll develop and test a fix
4. **Coordinated Disclosure**: We'll coordinate the public disclosure with you
5. **Credit**: We'll credit you in our CHANGELOG (if desired)

## Security Best Practices for Contributors

### Code Review Requirements

All code changes must:
- Pass automated security scans (planned: CodeQL, Dependabot)
- Be reviewed by at least one maintainer
- Follow secure coding guidelines below
- Include appropriate tests

### Secure Coding Guidelines

#### Authentication & Authorization

- **Never** store passwords in plain text
- Use bcrypt for password hashing (work factor ≥ 12)
- Implement JWT tokens with appropriate expiration (15 min access, 7 day refresh)
- Validate JWT signatures on every protected endpoint
- Always check both user authentication AND entity-level access
- Use role-based access control (RBAC) consistently

#### Multi-Tenant Security

```python
# ALWAYS filter by tenant_id in queries
instances = db.query(ComplianceInstance).filter(
    ComplianceInstance.tenant_id == current_user.tenant_id
).all()

# NEVER trust tenant_id from request body
# ALWAYS use tenant_id from authenticated JWT token
```

#### Input Validation

- Validate ALL inputs with Pydantic (backend) and Zod (frontend)
- Sanitize user inputs to prevent XSS
- Use parameterized queries (SQLAlchemy handles this automatically)
- Reject unexpected file types/sizes on upload
- Implement rate limiting on authentication endpoints

#### SQL Injection Prevention

```python
# GOOD - Parameterized queries (SQLAlchemy)
db.query(User).filter(User.email == user_email).first()

# BAD - String concatenation (NEVER DO THIS)
db.execute(f"SELECT * FROM users WHERE email = '{user_email}'")
```

#### Cross-Site Scripting (XSS) Prevention

```typescript
// GOOD - Use React's built-in escaping
<div>{userInput}</div>

// BAD - Direct HTML injection (NEVER DO THIS)
<div dangerouslySetInnerHTML={{__html: userInput}} />
```

#### File Upload Security

- Validate file types using magic bytes (not just extensions)
- Scan uploaded files for viruses (planned: ClamAV integration)
- Store files in S3 with signed URLs (not in database)
- Generate SHA-256 hashes for file integrity
- Enforce file size limits (current: 50 MB max)
- Use randomized S3 keys (not user-provided filenames)

#### Sensitive Data Handling

- **Never** log passwords, tokens, or sensitive PII
- **Never** commit `.env` files to Git
- Use environment variables for all secrets
- Implement audit logging for all sensitive operations
- Mark evidence as immutable after approval (prevents tampering)

### Frontend Security

#### Token Storage (IMPORTANT UPDATE PENDING)

**Current Implementation** (Phase 1):
```typescript
// Tokens stored in localStorage (XSS vulnerability)
localStorage.setItem('access_token', token)
```

**Planned Implementation** (Phase 2):
```typescript
// Migrate to httpOnly cookies for XSS protection
// Tokens will be set by backend via Set-Cookie header
// Frontend will not have JavaScript access to tokens
```

#### CSRF Protection

- Implement CSRF tokens for state-changing operations (planned for Phase 2)
- Use SameSite cookies: `SameSite=Strict` or `SameSite=Lax`

#### Content Security Policy

Planned CSP headers:
```
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' https://api.compliance-os.com;
```

## Known Security Considerations

### Phase 1 (Current)

The following security items are documented and will be addressed in upcoming phases:

1. **Frontend Token Storage** (Phase 2)
   - Issue: Tokens currently stored in localStorage (XSS vulnerability)
   - Plan: Migrate to httpOnly cookies in Phase 2
   - Risk: MEDIUM (no user data in system yet)

2. **Test Coverage** (Phase 11)
   - Issue: <10% test coverage
   - Plan: Comprehensive security testing in Phase 11
   - Risk: LOW (development environment only)

3. **Rate Limiting** (Phase 4)
   - Issue: No rate limiting on API endpoints
   - Plan: Implement in Phase 4 with Redis
   - Risk: MEDIUM (DoS vulnerability)

4. **File Validation** (Phase 4)
   - Issue: Basic file type validation only
   - Plan: Implement ClamAV virus scanning
   - Risk: MEDIUM (malware upload possible)

### Production Deployment Requirements

Before production deployment (Phase 12), we MUST implement:

- [ ] HTTPS/TLS encryption (Let's Encrypt or AWS ACM)
- [ ] Web Application Firewall (AWS WAF or Cloudflare)
- [ ] DDoS protection
- [ ] Database encryption at rest
- [ ] Secrets management (AWS Secrets Manager or HashiCorp Vault)
- [ ] Automated security scanning (SAST/DAST)
- [ ] Dependency vulnerability scanning (Dependabot, Snyk)
- [ ] Log aggregation and monitoring (ELK stack or CloudWatch)
- [ ] Intrusion detection system
- [ ] Regular security audits
- [ ] Incident response plan

## Data Residency & Compliance

### India Data Localization

- All databases must be hosted in India (AWS ap-south-1 Mumbai region)
- All S3 buckets must use India region
- No data transfer outside India borders
- Compliance with IT Act 2000 and data protection regulations

### Audit Trail Requirements

- All CREATE/UPDATE/DELETE/APPROVE/REJECT actions logged to `audit_logs`
- Audit logs are append-only (immutable)
- Logs include: user_id, tenant_id, action, entity_type, entity_id, before/after snapshots
- Evidence files are immutable after approval
- Minimum 7-year audit log retention

## Security Testing

### Automated Scans

We use the following automated security tools:

- **Dependabot**: Dependency vulnerability scanning (planned)
- **CodeQL**: Static application security testing (planned)
- **Flake8**: Python code linting with security plugins
- **ESLint**: JavaScript/TypeScript linting with security rules
- **MyPy**: Python type checking (reduces runtime errors)

### Manual Testing

Security testing checklist (before each release):

- [ ] Authentication bypass attempts
- [ ] Multi-tenant isolation verification (critical for data leakage prevention)
- [ ] SQL injection tests on all endpoints
- [ ] XSS tests on all user input fields
- [ ] CSRF tests on state-changing operations
- [ ] File upload validation tests
- [ ] Authorization bypass attempts
- [ ] Session management tests
- [ ] Audit log completeness verification

## Incident Response

In the event of a security breach:

1. **Immediate Actions** (0-1 hour):
   - Isolate affected systems
   - Preserve evidence (logs, database snapshots)
   - Notify security team lead

2. **Assessment** (1-4 hours):
   - Determine scope of breach
   - Identify affected data/users
   - Document timeline

3. **Containment** (4-24 hours):
   - Patch vulnerability
   - Reset compromised credentials
   - Deploy fixes

4. **Notification** (24-72 hours):
   - Notify affected tenants/users
   - Report to regulatory authorities (if required)
   - Public disclosure (if warranted)

5. **Post-Incident** (1-2 weeks):
   - Root cause analysis
   - Update security controls
   - Update documentation
   - Security training

## Security Contacts

- **Security Issues**: [security@compliance-os.com]
- **General Questions**: [support@compliance-os.com]
- **Project Lead**: [Placeholder for maintainer contact]

## Acknowledgments

We thank the following security researchers for responsible disclosure:

(This section will be updated as vulnerabilities are reported and fixed)

## Security Updates

Stay informed about security updates:

- Watch this repository for security advisories
- Subscribe to our security mailing list (coming soon)
- Check CHANGELOG.md for security-related releases

## License

This security policy is part of the Compliance OS project and is licensed under the MIT License.

---

**Last Updated**: December 18, 2024
**Version**: 1.0
