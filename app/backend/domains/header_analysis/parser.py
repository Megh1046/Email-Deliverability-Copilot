"""
Raw email header parser.

Extracts authentication evidence from RFC 5322 headers without making
any pass/fail judgments. All normalization and verdict logic lives in
validator.py, alignment.py, and root_cause.py.

Fixes:
  BUG-003 — Multi-hop Authentication-Results: all headers are parsed
             individually; the first one (prepended by the final MTA)
             is used as the primary trusted verdict.
  BUG-005 — Quoted/bracketed smtp.mailfrom values are stripped before
             domain extraction.
  BUG-007 — DKIM-Signature d= is extracted using proper tag-value
             parsing, not a bare regex that can match false tokens.
"""
from __future__ import annotations

import re
from email import policy
from email.parser import Parser
from email.utils import parseaddr
from typing import List, Optional

from .schemas import AuthEvidence


# ---------------------------------------------------------------------------
# Domain extraction helpers
# ---------------------------------------------------------------------------

def _email_domain(value: Optional[str]) -> Optional[str]:
    """Extract the domain portion from an email address string.

    Handles:
      - Bare addresses:       user@example.com        → example.com
      - Angle-bracket form:   <user@example.com>      → example.com
      - Display-name form:    Alice <alice@example.com>  → example.com
      - Quoted values:        "user@example.com"      → example.com
    """
    if not value:
        return None
    # Strip outer whitespace, quotes, and angle brackets
    value = value.strip().strip('"').strip("<>").strip()
    # Try RFC 5322 address parsing first
    _, addr = parseaddr(value)
    if not addr:
        addr = value
    if "@" not in addr:
        return None
    return addr.rsplit("@", 1)[1].lower().rstrip(".")


def _tag_domain(value: Optional[str]) -> Optional[str]:
    """Validate and return a bare domain/hostname token.

    Accepts only tokens that look like valid DNS labels.
    Rejects empty strings, IP addresses, and strings with spaces.
    """
    if not value:
        return None
    value = value.strip().strip('"').strip("<>").strip().lower().rstrip(".")
    # Must look like a DNS name: labels of [a-z0-9] optionally with dots/hyphens
    if re.fullmatch(r"[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?", value):
        return value
    return None


# ---------------------------------------------------------------------------
# Authentication-Results header parser (RFC 8601)
# ---------------------------------------------------------------------------

def _parse_auth_results_header(header_value: str) -> AuthEvidence:
    """Parse one Authentication-Results header into structured evidence.

    Header format (RFC 8601):
        Authentication-Results: authserv-id; method=result prop=value; ...

    The authserv-id is the FQDN of the server that added this header.
    Multiple semicolon-separated result clauses follow.

    We extract SPF, DKIM, and DMARC results plus their associated
    property values (smtp.mailfrom, header.d, header.s).
    """
    evidence = AuthEvidence(raw=header_value)

    # authserv-id is the first token before the first semicolon
    first_semi = header_value.find(";")
    if first_semi != -1:
        evidence.authserv_id = header_value[:first_semi].strip()

    body = header_value  # search the full header

    # ── SPF result ───────────────────────────────────────────────────────────
    spf_m = re.search(r"\bspf\s*=\s*([a-z]+)", body, re.IGNORECASE)
    if spf_m:
        evidence.spf_result = spf_m.group(1).lower()

    # ── SPF authenticated domain ─────────────────────────────────────────────
    # Handles quoted and angle-bracketed values; captures up to the next
    # whitespace, semicolon, or end-of-field.
    spf_domain_m = re.search(
        r'\b(?:smtp\.mailfrom|envelope-from|smtp\.helo)\s*=\s*'
        r'["\s<]*([^"\s;<>\r\n]+)["\s>]*',
        body,
        re.IGNORECASE,
    )
    if spf_domain_m:
        raw_val = spf_domain_m.group(1).strip(' "\'<>')
        evidence.spf_domain = _email_domain(raw_val) or _tag_domain(raw_val)

    # ── DKIM result ──────────────────────────────────────────────────────────
    dkim_m = re.search(r"\bdkim\s*=\s*([a-z]+)", body, re.IGNORECASE)
    if dkim_m:
        evidence.dkim_result = dkim_m.group(1).lower()

    # ── DKIM signing domain (header.d=) ─────────────────────────────────────
    dkim_d_m = re.search(
        r'\bheader\.d\s*=\s*([^\s;,\r\n"<>]+)',
        body,
        re.IGNORECASE,
    )
    if dkim_d_m:
        evidence.dkim_domain = _tag_domain(dkim_d_m.group(1))

    # ── DKIM selector (header.s=) ────────────────────────────────────────────
    dkim_s_m = re.search(
        r'\bheader\.s\s*=\s*([^\s;,\r\n"<>]+)',
        body,
        re.IGNORECASE,
    )
    if dkim_s_m:
        evidence.dkim_selector = dkim_s_m.group(1).strip()

    # ── DMARC result ─────────────────────────────────────────────────────────
    dmarc_m = re.search(r"\bdmarc\s*=\s*([a-z]+)", body, re.IGNORECASE)
    if dmarc_m:
        evidence.dmarc_result = dmarc_m.group(1).lower()

    return evidence


# ---------------------------------------------------------------------------
# DKIM-Signature parser
# ---------------------------------------------------------------------------

def _parse_dkim_signature_domain(header_value: str) -> Optional[str]:
    """Extract the d= (signing domain) from a DKIM-Signature header.

    Fixes BUG-007: uses proper semicolon-delimited tag-value parsing
    rather than a bare regex that can accidentally match characters
    inside the b= signature blob.
    """
    if not header_value:
        return None
    tags: dict[str, str] = {}
    for part in header_value.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        key, _, val = part.partition("=")
        key = key.strip().lower()
        val = val.strip()
        if key not in tags:
            tags[key] = val
    return _tag_domain(tags.get("d"))


# ---------------------------------------------------------------------------
# Intermediate parsed data container
# ---------------------------------------------------------------------------

class ParsedHeaderData:
    """
    Intermediate container for raw evidence extracted from email headers.

    Not a Pydantic model; this is an internal pipeline type used only
    between parser.py and validator.py.
    """

    __slots__ = (
        "from_domain",
        "return_path_domain",
        "primary_evidence",
        "all_evidence",
        "dkim_signature_domain",
        "raw_auth_results",
    )

    def __init__(
        self,
        from_domain: Optional[str],
        return_path_domain: Optional[str],
        primary_evidence: AuthEvidence,
        all_evidence: List[AuthEvidence],
        dkim_signature_domain: Optional[str],
        raw_auth_results: List[str],
    ) -> None:
        self.from_domain = from_domain
        self.return_path_domain = return_path_domain
        self.primary_evidence = primary_evidence
        self.all_evidence = all_evidence
        self.dkim_signature_domain = dkim_signature_domain
        self.raw_auth_results = raw_auth_results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class HeaderParser:
    """
    Parse raw email headers into structured authentication evidence.

    Fixes BUG-003: All Authentication-Results headers are parsed
    individually.  The FIRST header is treated as the final receiving
    MTA's verdict (per Gmail/RFC convention where receivers prepend
    their result).  All headers are exposed for transparency.

    This class does NOT make pass/fail judgments.
    """

    def parse(self, raw_headers: str) -> ParsedHeaderData:
        message = Parser(policy=policy.default).parsestr(raw_headers, headersonly=True)

        # From domain — the RFC 5322 identity that DMARC protects
        from_domain = _email_domain(message.get("From"))

        # Return-Path / envelope-from domain — used for SPF alignment
        return_path_raw = message.get("Return-Path", "")
        return_path_domain = _email_domain(return_path_raw) or _tag_domain(return_path_raw)

        # Parse ALL Authentication-Results headers.
        # get_all() returns them in message order (top-to-bottom).
        # The FIRST header was prepended by the final receiving MTA —
        # this is the most trusted result.
        raw_ar_headers: List[str] = message.get_all("Authentication-Results") or []
        all_evidence: List[AuthEvidence] = [
            _parse_auth_results_header(h) for h in raw_ar_headers
        ]

        primary_evidence = all_evidence[0] if all_evidence else AuthEvidence(raw="")

        # DKIM-Signature domain — fallback when header.d= is absent
        dkim_signature_domain = _parse_dkim_signature_domain(
            message.get("DKIM-Signature", "")
        )

        return ParsedHeaderData(
            from_domain=from_domain,
            return_path_domain=return_path_domain,
            primary_evidence=primary_evidence,
            all_evidence=all_evidence,
            dkim_signature_domain=dkim_signature_domain,
            raw_auth_results=raw_ar_headers,
        )
