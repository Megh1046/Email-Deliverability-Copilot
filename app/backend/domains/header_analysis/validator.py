"""
Authentication result validator.

Normalizes raw authentication result strings from RFC 8601 headers
into structured AuthenticationResult objects with standardized
PASS | FAIL | UNKNOWN verdicts.

Raw RFC 8601 result values per protocol:

  SPF  (RFC 7208 §2.6):  none, neutral, pass, fail, softfail,
                          temperror, permerror
  DKIM (RFC 6376 §3.5):  none, pass, fail, policy, neutral,
                          temperror, permerror
  DMARC (RFC 7489 §11.2): none, pass, fail, temperror, permerror

Mapping:
  PASS    — authentication succeeded
  FAIL    — authentication failed (includes softfail for SPF)
  UNKNOWN — no result present OR a temporary/inconclusive result
"""
from __future__ import annotations

from typing import Optional, Tuple

from .schemas import AuthenticationResult
from .parser import ParsedHeaderData


# ---------------------------------------------------------------------------
# RFC 8601 result value classification
# ---------------------------------------------------------------------------

# SPF: "fail" and "softfail" are both authentication failures.
# Receivers typically treat softfail as FAIL for DMARC alignment purposes.
_SPF_PASS = {"pass"}
_SPF_FAIL = {"fail", "softfail"}

# DKIM: "fail" and "policy" both indicate the signature did not verify.
_DKIM_PASS = {"pass"}
_DKIM_FAIL = {"fail", "policy", "permerror"}

# DMARC
_DMARC_PASS = {"pass"}
_DMARC_FAIL = {"fail", "reject"}


def _normalize(
    raw: Optional[str],
    pass_values: set[str],
    fail_values: set[str],
) -> str:
    """Map a raw result string to PASS | FAIL | UNKNOWN."""
    if not raw:
        return "UNKNOWN"
    lower = raw.lower().strip()
    if lower in pass_values:
        return "PASS"
    if lower in fail_values:
        return "FAIL"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class AuthenticationValidator:
    """
    Validates and normalizes authentication evidence from parsed headers.

    Takes the ParsedHeaderData from HeaderParser and returns three
    AuthenticationResult objects — one per protocol.
    """

    def validate(
        self, data: ParsedHeaderData
    ) -> Tuple[AuthenticationResult, AuthenticationResult, AuthenticationResult]:
        """
        Return (spf, dkim, dmarc) as normalized AuthenticationResult objects.

        Always uses the primary_evidence (first / most trusted
        Authentication-Results header).
        """
        ev = data.primary_evidence

        # ── SPF ─────────────────────────────────────────────────────────────
        spf_result_str = _normalize(ev.spf_result, _SPF_PASS, _SPF_FAIL)
        # Prefer the domain from the Authentication-Results header;
        # fall back to the Return-Path domain extracted from the raw header.
        spf_domain = ev.spf_domain or data.return_path_domain
        spf = AuthenticationResult(
            result=spf_result_str,
            raw_result=ev.spf_result,
            domain=spf_domain,
        )

        # ── DKIM ────────────────────────────────────────────────────────────
        dkim_result_str = _normalize(ev.dkim_result, _DKIM_PASS, _DKIM_FAIL)
        # Prefer header.d=; fall back to the DKIM-Signature d= tag.
        dkim_domain = ev.dkim_domain or data.dkim_signature_domain
        dkim = AuthenticationResult(
            result=dkim_result_str,
            raw_result=ev.dkim_result,
            domain=dkim_domain,
            selector=ev.dkim_selector,
        )

        # ── DMARC ───────────────────────────────────────────────────────────
        dmarc_result_str = _normalize(ev.dmarc_result, _DMARC_PASS, _DMARC_FAIL)
        dmarc = AuthenticationResult(
            result=dmarc_result_str,
            raw_result=ev.dmarc_result,
        )

        return spf, dkim, dmarc
