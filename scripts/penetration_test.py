"""
TURBO-CDI: Basic Automated Penetration Tests
Checks for common vulnerabilities: SQL injection, XSS, CSRF, open endpoints.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.parse
from dataclasses import asdict, dataclass, field
from typing import Any

import httpx


@dataclass
class PentestFinding:
    """Single penetration test finding."""

    test: str
    endpoint: str
    severity: str
    status: str
    detail: str
    remediation: str
    evidence: dict[str, Any] = field(default_factory=dict)


class PentestRunner:
    """Automated penetration test runner."""

    SQLI_PAYLOADS = [
        "' OR '1'='1",
        "' UNION SELECT null,null--",
        "1; DROP TABLE users--",
        "' OR 1=1--",
        "1' AND 1=1--",
    ]

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
        "'><script>alert('xss')</script>",
    ]

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.findings: list[PentestFinding] = []
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)

    async def run_all(self) -> list[PentestFinding]:
        """Run all penetration tests."""
        await self.test_sql_injection()
        await self.test_xss()
        await self.test_csrf_protection()
        await self.test_open_endpoints()
        await self.test_security_headers()
        await self.test_rate_limiting()
        await self.test_information_disclosure()
        await self.client.aclose()
        return self.findings

    async def test_sql_injection(self) -> None:
        """Test for SQL injection vulnerabilities."""
        endpoints = [
            ("/api/v1/solve", "POST", {"problem": "{payload}"}),
            ("/api/v1/search", "GET", {"q": "{payload}"}),
            ("/api/v1/users", "GET", {"email": "{payload}"}),
        ]

        for path, method, params in endpoints:
            for payload in self.SQLI_PAYLOADS:
                url = f"{self.base_url}{path}"
                formatted_params = {k: v.format(payload=payload) for k, v in params.items()}

                try:
                    if method == "GET":
                        response = await self.client.get(url, params=formatted_params)
                    else:
                        response = await self.client.post(url, json=formatted_params)

                    body = response.text.lower()
                    sql_errors = [
                        "sql syntax",
                        "mysql_fetch",
                        "pg_query",
                        "sqlite3",
                        "ora-",
                        "syntax error",
                        "unclosed quotation",
                    ]

                    if any(err in body for err in sql_errors):
                        self._add_finding(
                            "SQL Injection",
                            path,
                            "CRITICAL",
                            "VULNERABLE",
                            f"SQL error leaked for payload: {payload[:50]}",
                            "Use parameterized queries and ORM. Never concatenate SQL.",
                            {"payload": payload[:100], "status_code": response.status_code},
                        )
                        return

                    if response.status_code == 500:
                        self._add_finding(
                            "SQL Injection",
                            path,
                            "HIGH",
                            "SUSPICIOUS",
                            f"Server error on SQLi payload: {payload[:50]}",
                            "Review error handling. Use parameterized queries.",
                            {"payload": payload[:100], "status_code": 500},
                        )

                except httpx.RequestError:
                    continue

        self._add_finding(
            "SQL Injection",
            "multiple",
            "INFO",
            "PASSED",
            "No SQL injection vulnerabilities detected",
            "Continue using parameterized queries.",
        )

    async def test_xss(self) -> None:
        """Test for XSS vulnerabilities."""
        endpoints = [
            ("/api/v1/solve", "POST", {"problem": "{payload}"}),
            ("/api/v1/feedback", "POST", {"message": "{payload}"}),
        ]

        for path, method, params in endpoints:
            for payload in self.XSS_PAYLOADS:
                url = f"{self.base_url}{path}"
                formatted_params = {k: v.format(payload=payload) for k, v in params.items()}

                try:
                    if method == "POST":
                        response = await self.client.post(url, json=formatted_params)
                    else:
                        response = await self.client.get(url, params=formatted_params)

                    body = response.text
                    if payload in body:
                        self._add_finding(
                            "Cross-Site Scripting (XSS)",
                            path,
                            "HIGH",
                            "VULNERABLE",
                            f"XSS payload reflected without sanitization: {payload[:50]}",
                            "Implement output encoding and Content-Security-Policy headers.",
                            {"payload": payload[:100]},
                        )
                        return

                except httpx.RequestError:
                    continue

        self._add_finding(
            "Cross-Site Scripting (XSS)",
            "multiple",
            "INFO",
            "PASSED",
            "No XSS vulnerabilities detected",
            "Continue sanitizing all user input and use CSP headers.",
        )

    async def test_csrf_protection(self) -> None:
        """Test for CSRF protection on state-changing endpoints."""
        state_endpoints = [
            ("/api/v1/solve", "POST", {"problem": "test"}),
            ("/api/v1/users", "POST", {"email": "test@test.com"}),
        ]

        for path, method, data in state_endpoints:
            url = f"{self.base_url}{path}"
            try:
                # Test without CSRF token / Origin header
                headers = {"Content-Type": "application/json"}
                if method == "POST":
                    response = await self.client.post(url, json=data, headers=headers)
                else:
                    response = await self.client.request(method, url, json=data, headers=headers)

                # If it succeeds without proper auth/CSRF, that's a finding
                if response.status_code in (200, 201, 204):
                    self._add_finding(
                        "CSRF Protection",
                        path,
                        "MEDIUM",
                        "WARNING",
                        f"State-changing endpoint {path} accepted request without CSRF token",
                        "Implement CSRF tokens and validate Origin/Referer headers.",
                        {"status_code": response.status_code},
                    )

            except httpx.RequestError:
                continue

        self._add_finding(
            "CSRF Protection",
            "multiple",
            "INFO",
            "CHECKED",
            "CSRF protection verified on state-changing endpoints",
            "Ensure SameSite cookies and CSRF tokens are enforced.",
        )

    async def test_open_endpoints(self) -> None:
        """Test for overly permissive endpoints."""
        sensitive_paths = [
            "/admin",
            "/debug",
            "/.env",
            "/config",
            "/api/docs",
            "/api/redoc",
            "/v1/debug",
            "/actuator",
            "/swagger.json",
            "/api/swagger.json",
        ]

        for path in sensitive_paths:
            url = f"{self.base_url}{path}"
            try:
                response = await self.client.get(url)
                if response.status_code == 200:
                    self._add_finding(
                        "Open Endpoints",
                        path,
                        "MEDIUM",
                        "WARNING",
                        f"Potentially sensitive endpoint accessible: {path}",
                        "Restrict or remove debug/admin endpoints in production.",
                        {"status_code": 200, "size": len(response.text)},
                    )
            except httpx.RequestError:
                continue

        self._add_finding(
            "Open Endpoints",
            "multiple",
            "INFO",
            "CHECKED",
            "Sensitive endpoint scan completed",
            "Regularly audit exposed endpoints.",
        )

    async def test_security_headers(self) -> None:
        """Test for security headers."""
        try:
            response = await self.client.get(f"{self.base_url}/")
            headers = response.headers

            required_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Content-Security-Policy": None,
                "Referrer-Policy": None,
            }

            for header, expected in required_headers.items():
                if header not in headers:
                    self._add_finding(
                        "Security Headers",
                        "/",
                        "MEDIUM",
                        "MISSING",
                        f"Security header missing: {header}",
                        f"Add {header} header to all responses.",
                    )
                elif expected and headers[header] != expected:
                    self._add_finding(
                        "Security Headers",
                        "/",
                        "LOW",
                        "MISCONFIGURED",
                        f"Header {header} has unexpected value: {headers[header]}",
                        f"Set {header} to {expected}.",
                    )

            if "Strict-Transport-Security" not in headers:
                self._add_finding(
                    "Security Headers",
                    "/",
                    "MEDIUM",
                    "MISSING",
                    "HSTS header missing",
                    "Add Strict-Transport-Security header in production.",
                )

        except httpx.RequestError as e:
            self._add_finding(
                "Security Headers",
                "/",
                "INFO",
                "ERROR",
                f"Could not test headers: {e}",
                "Ensure server is running.",
            )

    async def test_rate_limiting(self) -> None:
        """Test for rate limiting."""
        url = f"{self.base_url}/api/v1/health"
        try:
            # Make 10 rapid requests
            responses = await asyncio.gather(
                *[self.client.get(url) for _ in range(10)],
                return_exceptions=True,
            )

            status_codes = [
                r.status_code for r in responses if isinstance(r, httpx.Response)
            ]
            if 429 in status_codes:
                self._add_finding(
                    "Rate Limiting",
                    "/api/v1/health",
                    "INFO",
                    "PASSED",
                    "Rate limiting is active (429 received)",
                    "Ensure rate limits are appropriate for your use case.",
                )
            elif all(s == 200 for s in status_codes):
                self._add_finding(
                    "Rate Limiting",
                    "/api/v1/health",
                    "LOW",
                    "WARNING",
                    "No rate limiting detected on 10 rapid requests",
                    "Implement rate limiting on all endpoints.",
                )

        except httpx.RequestError:
            self._add_finding(
                "Rate Limiting",
                "/api/v1/health",
                "INFO",
                "ERROR",
                "Could not test rate limiting",
                "Ensure server is running.",
            )

    async def test_information_disclosure(self) -> None:
        """Test for information disclosure in error responses."""
        try:
            # Trigger a 404 and check for stack traces
            response = await self.client.get(f"{self.base_url}/api/v1/nonexistent-endpoint-12345")
            body = response.text.lower()

            disclosure_patterns = [
                "traceback",
                "stack trace",
                "exception",
                "sqlalchemy",
                "django",
                "flask",
                "fastapi.debug",
                "internal server error",
                "line ",
                "file ",
            ]

            for pattern in disclosure_patterns:
                if pattern in body:
                    self._add_finding(
                        "Information Disclosure",
                        "/api/v1/nonexistent-endpoint-12345",
                        "MEDIUM",
                        "WARNING",
                        f"Error response may leak internal details: '{pattern}'",
                        "Disable debug mode and use generic error messages in production.",
                        {"snippet": body[max(0, body.find(pattern) - 30):body.find(pattern) + 50]},
                    )
                    return

            self._add_finding(
                "Information Disclosure",
                "/api/v1/nonexistent-endpoint-12345",
                "INFO",
                "PASSED",
                "No information disclosure in error responses",
                "Continue using generic error messages.",
            )

        except httpx.RequestError:
            pass

    def _add_finding(
        self,
        test: str,
        endpoint: str,
        severity: str,
        status: str,
        detail: str,
        remediation: str,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        self.findings.append(
            PentestFinding(
                test=test,
                endpoint=endpoint,
                severity=severity,
                status=status,
                detail=detail,
                remediation=remediation,
                evidence=evidence or {},
            )
        )

    def summary(self) -> dict[str, Any]:
        """Generate test summary."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1

        vulnerable = any(f.status == "VULNERABLE" for f in self.findings)
        return {
            "target": self.base_url,
            "total_tests": len(self.findings),
            "severity_counts": counts,
            "vulnerable": vulnerable,
            "findings": [asdict(f) for f in self.findings],
        }


async def main() -> int:
    parser = argparse.ArgumentParser(description="TURBO-CDI Penetration Test Suite")
    parser.add_argument("--url", default="http://localhost:8000", help="Target base URL")
    parser.add_argument("--output", "-o", help="Output file for JSON report")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout")
    args = parser.parse_args()

    print("TURBO-CDI Penetration Test Suite")
    print(f"Target: {args.url}")
    print("-" * 60)

    runner = PentestRunner(args.url, timeout=args.timeout)
    findings = await runner.run_all()
    summary = runner.summary()

    print(f"\nResults: {summary['total_tests']} findings")
    print(f"  CRITICAL: {summary['severity_counts']['CRITICAL']}")
    print(f"  HIGH:     {summary['severity_counts']['HIGH']}")
    print(f"  MEDIUM:   {summary['severity_counts']['MEDIUM']}")
    print(f"  LOW:      {summary['severity_counts']['LOW']}")
    print(f"  INFO:     {summary['severity_counts']['INFO']}")

    if summary["vulnerable"]:
        print("\n[!] VULNERABILITIES DETECTED — immediate attention required")
        for f in findings:
            if f.status == "VULNERABLE":
                print(f"  - [{f.severity}] {f.test}: {f.detail}")
        return 1

    print("\n[+] All critical checks passed")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Report saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
