"""
Header analysis domain schemas.

All response types for the Email Authentication Troubleshooter pipeline.
These types are the authoritative output contract for POST /headers.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class AuthEvidence(BaseModel):
    """
    Raw evidence extracted from a single Authentication-Results header.

    One instance per Authentication-Results header found in the email.
    The first entry (index 0) is always from the final receiving MTA —
    the most trusted verdict.
    """
    authserv_id: Optional[str] = None  # Server that produced this result
    spf_result: Optional[str] = None   # Raw: pass, fail, softfail, neutral, permerror, temperror
    spf_domain: Optional[str] = None   # smtp.mailfrom / envelope-from domain
    dkim_result: Optional[str] = None  # Raw: pass, fail, permerror, policy, neutral
    dkim_domain: Optional[str] = None  # header.d= value
    dkim_selector: Optional[str] = None  # header.s= value
    dmarc_result: Optional[str] = None  # Raw: pass, fail
    raw: str = ""


class AuthenticationResult(BaseModel):
    """Normalized authentication result for one protocol (SPF, DKIM, or DMARC)."""
    result: str  # PASS | FAIL | UNKNOWN
    raw_result: Optional[str] = None  # Original value from the header (e.g. "softfail")
    domain: Optional[str] = None       # Authenticated domain (SPF: envelope-from, DKIM: d=)
    selector: Optional[str] = None     # DKIM only: selector that was used


class AlignmentResult(BaseModel):
    """SPF and DKIM alignment status relative to the RFC 5322 From domain."""
    spf: Optional[bool] = None     # None = cannot determine (SPF did not pass)
    dkim: Optional[bool] = None    # None = cannot determine (DKIM did not pass)
    overall: Optional[bool] = None  # True = DMARC aligned; False = misaligned; None = unknown
    spf_mode: str = "relaxed"      # "relaxed" | "strict" — from DMARC aspf= tag
    dkim_mode: str = "relaxed"     # "relaxed" | "strict" — from DMARC adkim= tag


class RootCause(BaseModel):
    """Primary root cause of authentication failure."""
    code: str          # Machine-readable code, e.g. "SPF_AUTH_FAIL"
    title: str         # Short human-readable title
    description: str   # Full explanation of why this failure occurred
    protocol: str      # Primary protocol: "SPF" | "DKIM" | "DMARC" | "NONE"


class RemediationStep(BaseModel):
    """One actionable step in the remediation guide."""
    step: int
    action: str                          # Short instruction (the headline)
    detail: Optional[str] = None         # Longer explanation or sub-steps
    sample_record: Optional[str] = None  # Example DNS record value
    validation_cmd: Optional[str] = None  # Shell command to verify the fix


class ProviderInfo(BaseModel):
    """Detected email sending provider."""
    name: str
    confidence: str  # "HIGH" | "MEDIUM" | "LOW"


class HeaderAnalysisResponse(BaseModel):
    """
    Complete email authentication analysis result.

    This is the primary API response for POST /api/v1/analysis/headers.
    """

    # ── Core authentication verdicts ────────────────────────────────────────
    spf: AuthenticationResult
    dkim: AuthenticationResult
    dmarc: AuthenticationResult
    alignment: AlignmentResult

    # ── Domain context ───────────────────────────────────────────────────────
    from_domain: Optional[str] = None         # RFC 5322 From: header domain
    return_path_domain: Optional[str] = None  # Return-Path / envelope-from domain
    dkim_signing_domain: Optional[str] = None # d= from DKIM-Signature header

    # ── Raw evidence ─────────────────────────────────────────────────────────
    authentication_results: List[str] = Field(default_factory=list)
    evidence: List[AuthEvidence] = Field(default_factory=list)

    # ── Diagnosis ────────────────────────────────────────────────────────────
    root_cause: Optional[RootCause] = None
    remediation: List[RemediationStep] = Field(default_factory=list)

    # ── Provider ─────────────────────────────────────────────────────────────
    provider: Optional[ProviderInfo] = None

    # ── Summary ──────────────────────────────────────────────────────────────
    passed: bool = False
    failure_summary: Optional[str] = None
