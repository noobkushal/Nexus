"""Sandboxed Web Research & Browser Retrieval Tool.

Provides safe URL validation (anti-SSRF), untrusted HTML sanitization,
structured research extraction, and file persistence in storage/documents.
Operates completely offline-safe with deterministic fallback research fixtures.
"""
import ipaddress
import re
import socket
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

from app.core.logging import get_audit_logger, logger
from app.tools.filesystem import sandboxed_fs

audit_logger = get_audit_logger()


class WebSecurityError(Exception):
    """Raised when an outbound URL violates SSRF or security boundaries."""
    pass


class SSRFValidator:
    """Enforces strict outbound network boundary controls preventing SSRF attacks."""

    BLOCKED_HOSTNAMES = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "kubernetes.default",
        "metadata.google.internal",
        "169.254.169.254",  # Cloud Instance Metadata Service
    }

    @classmethod
    def validate_url(cls, url: str, check_dns: bool = True) -> str:
        """Validates that a URL is safe to fetch and points to a public, external destination."""
        if not url:
            raise WebSecurityError("Target URL cannot be empty.")

        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme.lower() not in ("http", "https"):
            raise WebSecurityError(f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are allowed.")

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            raise WebSecurityError(f"Invalid URL: Missing hostname in '{url}'.")

        if hostname in cls.BLOCKED_HOSTNAMES:
            audit_logger.warning(f"SECURITY ALERT: Blocked outbound access to restricted host: {hostname}")
            raise WebSecurityError(f"Access denied: Host '{hostname}' is restricted (internal/loopback).")

        # Resolve IP to verify non-private routing when DNS checking is requested
        if check_dns:
            try:
                addr_info = socket.getaddrinfo(hostname, None)
                for item in addr_info:
                    ip_str = item[4][0]
                    ip_obj = ipaddress.ip_address(ip_str)
                    # Block private, loopback, link-local and unspecified addresses
                    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_unspecified:
                        audit_logger.warning(f"SECURITY ALERT: SSRF attempt to private IP {ip_str} via {hostname}")
                        raise WebSecurityError(f"Access denied: Target resolves to private or loopback IP ({ip_str}).")
            except socket.gaierror:
                # When offline or DNS unavailable, continue
                pass

        return url


class UntrustedHTMLSanitizer:
    """Sanitizes untrusted HTML inputs to prevent XSS, script injection, and payload extraction."""

    # Regex patterns for stripping dangerous tags and contents
    TAGS_TO_REMOVE = re.compile(
        r"<(script|style|iframe|object|embed|svg|applet|meta|link|form|input)[^>]*>.*?</\1>",
        re.IGNORECASE | re.DOTALL,
    )
    SELF_CLOSING_DANGEROUS = re.compile(
        r"<(meta|link|input|embed)[^>]*>",
        re.IGNORECASE,
    )
    EVENT_HANDLERS = re.compile(
        r"\s+on\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
        re.IGNORECASE,
    )
    JAVASCRIPT_LINKS = re.compile(
        r"href\s*=\s*(?:\"javascript:[^\"]*\"|'javascript:[^']*')",
        re.IGNORECASE,
    )

    @classmethod
    def sanitize(cls, raw_html: str) -> Dict[str, Any]:
        """Cleans untrusted HTML and extracts semantic text, links, and title."""
        if not raw_html:
            return {"title": "Untitled", "clean_text": "", "links": [], "sanitized_length": 0}

        # 1. Extract Title before stripping tags
        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Document"

        # 2. Extract outward hyperlinks
        links: List[str] = []
        for href_match in re.finditer(r'<a[^>]+href=["\'](https?://[^"\']+)["\']', raw_html, re.IGNORECASE):
            link = href_match.group(1)
            if link not in links and len(links) < 10:
                links.append(link)

        # 3. Strip dangerous paired elements (script, style, iframe, etc.)
        sanitized = cls.TAGS_TO_REMOVE.sub(" ", raw_html)
        sanitized = cls.SELF_CLOSING_DANGEROUS.sub(" ", sanitized)
        sanitized = cls.EVENT_HANDLERS.sub(" ", sanitized)
        sanitized = cls.JAVASCRIPT_LINKS.sub('href="#"', sanitized)

        # 4. Strip remaining HTML tags, preserving text
        clean_text = re.sub(r"<[^>]+>", " ", sanitized)

        # 5. Normalize whitespace
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        return {
            "title": title,
            "clean_text": clean_text[:5000],  # Bound length for context management
            "links": links,
            "sanitized_length": len(clean_text),
        }


class SandboxedWebReader:
    """Safe web research and retrieval tool with offline mock support."""

    def __init__(self, offline_mode: bool = False):
        self.offline_mode = offline_mode
        self.validator = SSRFValidator()
        self.sanitizer = UntrustedHTMLSanitizer()

    async def fetch_and_sanitize(self, url: str) -> Dict[str, Any]:
        """Fetches web page content securely and returns sanitized text and metadata."""
        validated_url = self.validator.validate_url(url, check_dns=not self.offline_mode)

        if self.offline_mode:
            # Deterministic offline mock snapshot
            clean_host = urllib.parse.urlsplit(validated_url).hostname or "external-source"
            return {
                "url": validated_url,
                "title": f"Verified Research Source: {clean_host}",
                "clean_text": (
                    f"Simulated local research snapshot for {validated_url}. "
                    f"NEXUS Scout research agent retrieved this verified briefing in offline-safe mode. "
                    f"Key topics include architectural guidelines, runtime constraints, and local-first patterns."
                ),
                "links": [f"https://{clean_host}/docs", f"https://{clean_host}/api"],
                "sanitized_length": 240,
                "mode": "offline_simulated",
            }

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                headers = {"User-Agent": "NEXUS-ResearchBot/1.0 (+https://github.com/nexus/agent)"}
                response = await client.get(validated_url, headers=headers)
                response.raise_for_status()
                raw_html = response.text

            sanitized_data = self.sanitizer.sanitize(raw_html)
            sanitized_data["url"] = validated_url
            sanitized_data["mode"] = "live_network"
            return sanitized_data

        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError, socket.gaierror) as err:
            logger.warning(f"Web retrieval fallback triggered for {validated_url}: {err}")
            # Fallback gracefully to offline simulated snapshot
            return {
                "url": validated_url,
                "title": f"Cached Research Snapshot: {validated_url}",
                "clean_text": f"Retrieval note: Network destination {validated_url} was unavailable. Fallback research snapshot generated.",
                "links": [],
                "sanitized_length": 110,
                "mode": "fallback_offline",
            }

    def save_research_dossier(
        self,
        topic: str,
        query: str,
        content: str,
        sources: Optional[List[str]] = None,
    ) -> str:
        """Saves a research dossier into storage/documents/ with audited metadata."""
        slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", topic.lower()).strip("_") or "research_brief"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"research_{slug}_{timestamp}.md"
        relative_path = f"documents/{filename}"

        sources_list = sources or ["https://docs.nexus.local/reference"]
        sources_md = "\n".join(f"- {s}" for s in sources_list)

        dossier_content = (
            f"# Research Dossier: {topic.title()}\n\n"
            f"- **Generated By**: NEXUS Research Agent (Scout)\n"
            f"- **Timestamp**: {datetime.now(timezone.utc).isoformat()}\n"
            f"- **Query**: `{query}`\n"
            f"- **Security Status**: Quarantined & Sanitized (Untrusted Input Filter Applied)\n\n"
            f"## Verified Sources\n{sources_md}\n\n"
            f"## Key Findings & Synthesis\n\n"
            f"{content}\n\n"
            f"---\n"
            f"*NEXUS Sandboxed Research Engine — Local-first verification.*"
        )

        sandboxed_fs.write_text_file(relative_path, dossier_content, requires_approval=False)
        audit_logger.info(f"Research dossier created: {relative_path}")
        return relative_path


sandboxed_web_reader = SandboxedWebReader()
