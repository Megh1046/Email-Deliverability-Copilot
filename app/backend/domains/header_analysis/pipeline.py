"""
Header Analysis Pipeline.

Single entry point for the Email Authentication Troubleshooter.
Replaces the IntelligenceOrchestrator (core/orchestrator.py) for
all header-based analysis.

Pipeline stages
───────────────
  1. Parse     → HeaderParser extracts raw evidence
  2. Validate  → AuthenticationValidator normalizes results
  3. Align     → check_alignment computes alignment per RFC 7489
  4. Diagnose  → detect_root_cause identifies the primary failure
  5. Remediate → generate_remediation produces fix steps

All stages are pure functions or stateless classes; the pipeline
itself holds no mutable state and is safe to share across requests.
"""
from __future__ import annotations

from typing import Optional

from .alignment import check_alignment
from .parser import HeaderParser
from .remediation import generate_remediation
from .root_cause import detect_root_cause
from .schemas import HeaderAnalysisResponse, ProviderInfo
from .validator import AuthenticationValidator


class HeaderAnalysisPipeline:
    """
    End-to-end email authentication troubleshooter pipeline.

    Usage::

        pipeline = HeaderAnalysisPipeline()
        result = pipeline.analyze(raw_headers)
        # result.passed, result.root_cause, result.remediation …
    """

    def __init__(self) -> None:
        self._parser = HeaderParser()
        self._validator = AuthenticationValidator()

    def analyze(
        self,
        raw_headers: str,
        provider_hint: Optional[str] = None,
        spf_alignment_mode: str = "relaxed",
        dkim_alignment_mode: str = "relaxed",
    ) -> HeaderAnalysisResponse:
        """
        Run the full pipeline on raw email headers.

        Args:
            raw_headers:         Complete raw email header block (string).
            provider_hint:       Optional detected provider name; used to
                                 select provider-specific remediation steps.
            spf_alignment_mode:  "relaxed" | "strict"  (DMARC aspf= value).
            dkim_alignment_mode: "relaxed" | "strict"  (DMARC adkim= value).

        Returns:
            HeaderAnalysisResponse with full diagnosis and remediation.
        """

        # ── Stage 1: Parse ───────────────────────────────────────────────────
        parsed = self._parser.parse(raw_headers)

        # ── Stage 2: Validate ────────────────────────────────────────────────
        spf, dkim, dmarc = self._validator.validate(parsed)

        # ── Stage 3: Align ───────────────────────────────────────────────────
        alignment = check_alignment(
            from_domain=parsed.from_domain,
            spf=spf,
            dkim=dkim,
            spf_mode=spf_alignment_mode,
            dkim_mode=dkim_alignment_mode,
        )

        # ── Stage 4: Root cause ──────────────────────────────────────────────
        has_auth_results = bool(parsed.all_evidence and parsed.primary_evidence.raw)
        root_cause = detect_root_cause(
            from_domain=parsed.from_domain,
            spf=spf,
            dkim=dkim,
            dmarc=dmarc,
            alignment=alignment,
            has_auth_results=has_auth_results,
        )

        # ── Stage 5: Remediation ─────────────────────────────────────────────
        remediation = generate_remediation(
            root_cause_code=root_cause.code if root_cause else None,
            from_domain=parsed.from_domain,
            spf=spf,
            dkim=dkim,
            provider_name=provider_hint,
        )

        # ── Assemble response ────────────────────────────────────────────────

        # Overall pass: at least one protocol authenticated AND overall
        # alignment succeeded AND DMARC did not explicitly fail.
        auth_passed = spf.result == "PASS" or dkim.result == "PASS"
        passed = auth_passed and alignment.overall is True and dmarc.result != "FAIL"

        provider = (
            ProviderInfo(name=provider_hint, confidence="MEDIUM")
            if provider_hint
            else None
        )

        return HeaderAnalysisResponse(
            spf=spf,
            dkim=dkim,
            dmarc=dmarc,
            alignment=alignment,
            from_domain=parsed.from_domain,
            return_path_domain=parsed.return_path_domain,
            dkim_signing_domain=parsed.dkim_signature_domain,
            authentication_results=parsed.raw_auth_results,
            evidence=parsed.all_evidence,
            root_cause=root_cause,
            remediation=remediation,
            provider=provider,
            passed=passed,
            failure_summary=root_cause.title if root_cause else None,
        )
