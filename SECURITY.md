# Security Policy

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Email **dev@yooz.info** with:

- A clear description of the issue.
- A minimal reproduction (steps, code, request / response, etc.) if you have one.
- Affected version(s) and environment (OS, Python version).
- Your name and contact for follow-up. We're happy to credit you in the fix announcement if you'd like.

We aim to acknowledge within **2 business days** and provide a triage decision (accepted / needs more info / not a security issue) within **5 business days**.

## Scope

In scope:

- Credential leakage in CLI output, error messages, or logs (Issuer ID, Key ID, `.p8` contents, JWT tokens).
- Insecure handling of the App Store Connect private key on disk or in memory.
- Command injection or arbitrary file read / write via crafted YAML configs (`pricing.yaml`, `offers.yaml`).
- Auth bypass or privilege escalation paths in the simulation engine that could mask real production bugs.
- Pickle / YAML unsafe-load issues anywhere in the toolchain.

Out of scope (please don't report these):

- Vulnerabilities in third-party dependencies (`httpx`, `pyjwt`, `click`, etc.) where the upstream project is the right place to report.
- Issues in App Store Connect itself — report those to Apple via their security channel.
- Findings on test fixtures, sample configs, or development-only code paths.
- Self-XSS or social-engineering scenarios that require the user to actively cooperate with the attacker.

## Disclosure timeline

We follow **coordinated disclosure**:

1. You report → we acknowledge within 2 business days.
2. We triage and confirm within 5 business days.
3. We develop + test a fix. Standard fix window: **30 days** for critical / high, **60 days** for medium, **90 days** for low.
4. We coordinate the disclosure date with you.

## Hall of Fame

We'll list reporters with their permission once we've shipped fixes.

---

For non-security questions or general issues, please use **GitHub Issues**.
