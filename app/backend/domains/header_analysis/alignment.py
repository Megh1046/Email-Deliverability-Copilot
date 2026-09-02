"""
SPF and DKIM alignment checker.

Implements RFC 7489 §3.1 alignment rules with support for both
relaxed (r) and strict (s) alignment modes as declared by the
domain's DMARC policy (adkim= and aspf= tags).

Fix — BUG-004:
  The original code always used relaxed alignment regardless of the
  DMARC policy's alignment mode settings.  This implementation
  accepts explicit mode parameters so the pipeline can pass the
  actual adkim/aspf values when they are available.
"""
from __future__ import annotations

from typing import Optional

from .schemas import AlignmentResult, AuthenticationResult


# ---------------------------------------------------------------------------
# Alignment matching rules (RFC 7489 §3.1)
# ---------------------------------------------------------------------------

def _relaxed_match(from_domain: str, auth_domain: str) -> bool:
    """
    RFC 7489 relaxed alignment: organizational domains must match.

    The organizational domain is derived from the domain using the
    Public Suffix List (PSL).  Without a PSL dependency we use an
    approximation: the two domains align when one is an ancestor
    subdomain of the other (or they are identical).

    Examples (from_domain = example.com):
        mail.example.com  → aligned   (subdomain)
        example.com       → aligned   (exact)
        other.com         → NOT aligned
        sub.example.net   → NOT aligned
    """
    from_d = from_domain.lower()
    auth_d = auth_domain.lower()
    if from_d == auth_d:
        return True
    if auth_d.endswith("." + from_d):
        return True
    if from_d.endswith("." + auth_d):
        return True
    return False


def _strict_match(from_domain: str, auth_domain: str) -> bool:
    """RFC 7489 strict alignment: exact domain match required."""
    return from_domain.lower() == auth_domain.lower()


# ---------------------------------------------------------------------------
# Public alignment checker
# ---------------------------------------------------------------------------

def check_alignment(
    from_domain: Optional[str],
    spf: AuthenticationResult,
    dkim: AuthenticationResult,
    spf_mode: str = "relaxed",
    dkim_mode: str = "relaxed",
) -> AlignmentResult:
    """
    Check SPF and DKIM alignment against the RFC 5322 From domain.

    Alignment can only be evaluated when:
      - The From domain is known.
      - The relevant authenticated domain is known.
      - The authentication result was PASS.

    When authentication failed, alignment is set to None (not False),
    because a failed authentication simply has no alignment status —
    the email was not authenticated at all.

    DMARC passes when at least ONE aligned authentication path exists.

    Args:
        from_domain: RFC 5322 From header domain.
        spf:         Normalized SPF result (from validator.py).
        dkim:        Normalized DKIM result (from validator.py).
        spf_mode:    "relaxed" | "strict"  (DMARC aspf= tag value).
        dkim_mode:   "relaxed" | "strict"  (DMARC adkim= tag value).

    Returns:
        AlignmentResult with per-protocol and overall alignment.
    """
    spf_aligned: Optional[bool] = None
    dkim_aligned: Optional[bool] = None

    # Only check SPF alignment when SPF passed
    if spf.result == "PASS" and from_domain and spf.domain:
        matcher = _strict_match if spf_mode == "strict" else _relaxed_match
        spf_aligned = matcher(from_domain, spf.domain)

    # Only check DKIM alignment when DKIM passed
    if dkim.result == "PASS" and from_domain and dkim.domain:
        matcher = _strict_match if dkim_mode == "strict" else _relaxed_match
        dkim_aligned = matcher(from_domain, dkim.domain)

    # ── Overall DMARC alignment determination ────────────────────────────────
    # True   → at least one aligned path exists (DMARC would pass)
    # False  → at least one checked and found misaligned, none aligned
    # None   → no authenticated identity available to check

    if spf_aligned is True or dkim_aligned is True:
        overall: Optional[bool] = True
    elif spf_aligned is False and dkim_aligned is False:
        # Both authenticated and both misaligned
        overall = False
    elif spf_aligned is False and dkim_aligned is None:
        # SPF passed + misaligned; DKIM did not pass (no second path)
        overall = False
    elif spf_aligned is None and dkim_aligned is False:
        # DKIM passed + misaligned; SPF did not pass (no second path)
        overall = False
    else:
        # Both None — no authenticated identity was available
        overall = None

    return AlignmentResult(
        spf=spf_aligned,
        dkim=dkim_aligned,
        overall=overall,
        spf_mode=spf_mode,
        dkim_mode=dkim_mode,
    )
