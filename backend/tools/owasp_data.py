"""
OWASP Top 10 2021 — structured reference data.

Used by VulnAnalyzer and ExploitReasoner to ground LLM analysis
instead of relying purely on model training memory.
"""

from __future__ import annotations

OWASP_TOP_10: dict[str, dict] = {
    "A01:2021": {
        "name": "Broken Access Control",
        "description": (
            "Restrictions on what authenticated users are allowed to do are not properly enforced. "
            "Attackers exploit these flaws to access unauthorised functionality or data."
        ),
        "cwes": ["CWE-22 Path Traversal", "CWE-284 Improper Access Control",
                 "CWE-285 Improper Authorisation", "CWE-639 IDOR"],
        "examples": [
            "Accessing another user's account by modifying a URL parameter (IDOR)",
            "Viewing admin pages without being an admin",
            "Path traversal to read /etc/passwd or .env files",
            "JWT with 'alg: none' accepted by server",
        ],
    },
    "A02:2021": {
        "name": "Cryptographic Failures",
        "description": (
            "Failures related to cryptography (or lack thereof) that expose sensitive data "
            "such as passwords, credit card numbers, health records, or personal information."
        ),
        "cwes": ["CWE-259 Hardcoded Password", "CWE-327 Broken Crypto Algorithm",
                 "CWE-331 Insufficient Entropy", "CWE-326 Inadequate Key Strength"],
        "examples": [
            "Passwords stored as MD5 or SHA1 without salt",
            "Sensitive data transmitted over HTTP (missing HSTS)",
            "SSL certificate expired or self-signed in production",
            "Hardcoded API keys or secrets in source code",
            "Weak cipher suites (RC4, DES, 3DES) still enabled",
        ],
    },
    "A03:2021": {
        "name": "Injection",
        "description": (
            "User-supplied data is not validated, filtered, or sanitised by the application. "
            "Includes SQL, NoSQL, OS command, LDAP injection, and XSS."
        ),
        "cwes": ["CWE-89 SQL Injection", "CWE-78 OS Command Injection",
                 "CWE-79 XSS", "CWE-917 Expression Language Injection"],
        "examples": [
            "SQL query built by string concatenation with user input",
            "exec() or eval() called with unsanitised data",
            "shell_exec() / subprocess with user-controlled arguments",
            "Reflected XSS via unescaped query parameters in HTML",
            "LDAP injection via unsanitised username field",
        ],
    },
    "A04:2021": {
        "name": "Insecure Design",
        "description": (
            "Missing or ineffective security controls by design — not an implementation bug "
            "but a fundamental flaw in the application's architecture or business logic."
        ),
        "cwes": ["CWE-209 Info Exposure via Error", "CWE-522 Insufficiently Protected Credentials",
                 "CWE-770 Unrestricted Resource Allocation"],
        "examples": [
            "Password reset that sends the new password in plain text by email",
            "No rate limiting on authentication endpoints (brute-force risk)",
            "Business logic allows negative quantities in e-commerce cart",
            "Predictable resource identifiers (sequential IDs) used for access control",
        ],
    },
    "A05:2021": {
        "name": "Security Misconfiguration",
        "description": (
            "Insecure default configurations, incomplete configurations, open cloud storage, "
            "verbose error messages, or missing security hardening across the stack."
        ),
        "cwes": ["CWE-16 Configuration", "CWE-611 XXE", "CWE-732 Incorrect Permission Assignment"],
        "examples": [
            "Missing security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options",
            "Default credentials left unchanged on admin panels",
            "Stack traces or debug info exposed to end users",
            "Unnecessary HTTP methods enabled (TRACE, PUT, DELETE)",
            "Sensitive files publicly accessible: .env, .git/config, phpinfo.php",
            "CORS wildcard (Access-Control-Allow-Origin: *) on authenticated endpoints",
        ],
    },
    "A06:2021": {
        "name": "Vulnerable and Outdated Components",
        "description": (
            "Using components (libraries, frameworks, other modules) with known vulnerabilities. "
            "Includes OS, web servers, application servers, databases, APIs."
        ),
        "cwes": ["CWE-1035 Using Vulnerable Third-Party Component",
                 "CWE-937 Using Components with Known Vulnerabilities"],
        "examples": [
            "Outdated npm/pip packages with published CVEs",
            "Using Log4j versions vulnerable to Log4Shell (CVE-2021-44228)",
            "jQuery < 3.5.0 with XSS vulnerabilities",
            "OpenSSL versions affected by Heartbleed",
            "End-of-life operating system or web server with no patches",
        ],
    },
    "A07:2021": {
        "name": "Identification and Authentication Failures",
        "description": (
            "Weaknesses in authentication or session management that allow attackers "
            "to compromise passwords, keys, session tokens, or exploit other implementation flaws."
        ),
        "cwes": ["CWE-287 Improper Authentication", "CWE-384 Session Fixation",
                 "CWE-798 Hardcoded Credentials", "CWE-307 Brute Force"],
        "examples": [
            "Hardcoded credentials in source code or config files",
            "Session tokens exposed in URLs",
            "Weak or default passwords allowed",
            "Missing multi-factor authentication on sensitive actions",
            "Session not invalidated after logout",
            "JWT secret is a short, guessable string",
        ],
    },
    "A08:2021": {
        "name": "Software and Data Integrity Failures",
        "description": (
            "Code and infrastructure that does not protect against integrity violations — "
            "e.g. insecure deserialisation, unsigned updates, or CI/CD pipeline tampering."
        ),
        "cwes": ["CWE-502 Deserialization of Untrusted Data",
                 "CWE-494 Download Without Integrity Check",
                 "CWE-829 Inclusion of Functionality from Untrusted Source"],
        "examples": [
            "Deserialising untrusted YAML, Pickle, or Java objects leading to RCE",
            "Auto-update mechanism without signature verification",
            "CDN resources loaded without Subresource Integrity (SRI) checks",
            "Unsigned npm packages pulled from untrusted registries",
        ],
    },
    "A09:2021": {
        "name": "Security Logging and Monitoring Failures",
        "description": (
            "Insufficient logging, monitoring, or alerting that allows attackers to go undetected, "
            "persist, and pivot to more systems while tampering with evidence."
        ),
        "cwes": ["CWE-117 Improper Output Neutralisation for Logs",
                 "CWE-223 Omission of Security-relevant Information",
                 "CWE-778 Insufficient Logging"],
        "examples": [
            "Login failures not logged, allowing silent brute-force attacks",
            "No alerts triggered on repeated failed API calls",
            "Sensitive data (passwords, tokens) written to log files",
            "Logs stored only locally with no centralised SIEM",
            "Log injection via unsanitised user input written to logs",
        ],
    },
    "A10:2021": {
        "name": "Server-Side Request Forgery (SSRF)",
        "description": (
            "The server fetches a remote resource using a URL supplied by the user without "
            "proper validation, allowing attackers to reach internal services or cloud metadata."
        ),
        "cwes": ["CWE-918 Server-Side Request Forgery"],
        "examples": [
            "Webhook or URL preview feature that fetches user-supplied URLs",
            "Accessing AWS metadata endpoint http://169.254.169.254/",
            "Port-scanning internal network via SSRF",
            "Bypassing IP allow-lists by using DNS rebinding",
            "PDF/image rendering services that follow redirects to internal hosts",
        ],
    },
}


def get_owasp_context() -> str:
    """Return a compact reference string for injection into LLM system prompts."""
    lines = ["OWASP Top 10 2021 reference:"]
    for cat_id, data in OWASP_TOP_10.items():
        cwes = ", ".join(data["cwes"][:3])
        lines.append(f"  {cat_id} — {data['name']}: {data['description'].split('.')[0]}. CWEs: {cwes}.")
    return "\n".join(lines)


def get_category_detail(category_id: str) -> dict | None:
    """Return full detail for a single OWASP category (e.g. 'A03:2021')."""
    key = category_id.split("-")[0] if "-" in category_id else category_id
    return OWASP_TOP_10.get(key)


def match_owasp_category(text: str) -> str | None:
    """
    Given any text that mentions an OWASP category (e.g. 'A03:2021-Injection',
    'injection', 'sql injection'), return the canonical 'AXX:2021' key or None.
    """
    text_lower = text.lower()
    for cat_id, data in OWASP_TOP_10.items():
        if cat_id.lower() in text_lower:
            return cat_id
        if data["name"].lower() in text_lower:
            return cat_id
        for cwe in data["cwes"]:
            if cwe.lower().split(" ", 1)[-1] in text_lower:
                return cat_id
    return None
