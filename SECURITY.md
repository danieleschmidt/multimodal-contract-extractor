# Security Policy

## Supported Versions

We actively maintain security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.10.x  | :white_check_mark: |
| 0.9.x   | :white_check_mark: |
| < 0.9   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. Please do not report security vulnerabilities through public GitHub issues.

### How to Report

Please report security vulnerabilities by emailing **security@terragonlabs.com** with the following information:

- Type of issue (buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

- **Initial Response**: Within 48 hours of report submission
- **Status Update**: Within 7 days with preliminary assessment
- **Resolution**: Security patches released within 90 days for critical issues

### Security Measures

This project implements several security measures:

- **Input Validation**: All file inputs are validated and sanitized
- **Secure File Handling**: Temporary files use restricted permissions (0o600)
- **Dependency Scanning**: Regular automated security scanning via Bandit and CodeQL
- **Safe Defaults**: Security-first configuration defaults
- **Memory Safety**: Proper cleanup of temporary files and sensitive data

### Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. With your permission, we will acknowledge your contribution in our security advisories.

## Security Best Practices

When using this software:

1. **Keep Dependencies Updated**: Regularly update all dependencies
2. **File Size Limits**: Configure appropriate file size limits for your environment  
3. **Access Controls**: Implement proper authentication and authorization
4. **Audit Logging**: Enable audit logging in production environments
5. **Network Security**: Use HTTPS/TLS for all communications