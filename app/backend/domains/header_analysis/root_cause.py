"""
Root cause detection engine.

Identifies the PRIMARY reason why an email failed authentication.
Returns a single RootCause describing the failure, or None when
all checks passed.

Fix — BUG-006:
  The original _diagnose() method missed SPF authentication failure
  entirely and had incorrect priority ordering.  This engine uses a
  complete 8-case decision tree with explicit priorities.

Decision tree (highest priority first):
  1. NO_HEADERS          — No Authentication-Results headers present
  2. NO_AUTHENTICATION   — Both SPF and DKIM are UNKNOWN
  3. SPF_AUTH_FAIL       — spf=fail or spf=softfail
  4. DKIM_AUTH_FAIL      — dkim=fail
  5. BOTH_ALIGNMENT_FAIL — Both passed but both misaligned
  6. SPF_ALIGNMENT_FAIL  — SPF passed + misaligned; DKIM not helping
  7. DKIM_ALIGNMENT_FAIL — DKIM passed + misaligned; SPF not helping
  8. DMARC_POLICY_FAIL   — Explicit dmarc=fail (catch-all)
"""
from __future__ import annotations

from typing import Optional

from .schemas import AlignmentResult, AuthenticationResult, RootCause


# ---------------------------------------------------------------------------
# Root cause codes (consumed by remediation.py)
# ---------------------------------------------------------------------------

class RootCauseCode:
    NO_HEADERS = "NO_HEADERS"
    NO_AUTHENTICATION = "NO_AUTHENTICATION"
    SPF_AUTH_FAIL = "SPF_AUTH_FAIL"
    DKIM_AUTH_FAIL = "DKIM_AUTH_FAIL"
    SPF_ALIGNMENT_FAIL = "SPF_ALIGNMENT_FAIL"
    DKIM_ALIGNMENT_FAIL = "DKIM_ALIGNMENT_FAIL"
    BOTH_ALIGNMENT_FAIL = "BOTH_ALIGNMENT_FAIL"
    DMARC_POLICY_FAIL = "DMARC_POLICY_FAIL"


# ---------------------------------------------------------------------------
# Detection function
# ---------------------------------------------------------------------------

def detect_root_cause(
    from_domain: Optional[str],
    spf: AuthenticationResult,
    dkim: AuthenticationResult,
    dmarc: AuthenticationResult,
    alignment: AlignmentResult,
    has_auth_results: bool,
) -> Optional[RootCause]:
    """
    Identify the primary root cause of authentication failure.

    Returns None when no failure is detected (all checks passed).
    """

    # ── Case 1: No Authentication-Results headers ─────────────────────────
    if not has_auth_results:
        return RootCause(
            code=RootCauseCode.NO_HEADERS,
            title="No Authentication Results Found",
            description=(
                "These headers do not contain an Authentication-Results header. "
                "This header is added by the receiving mail server and records "
                "the SPF, DKIM, and DMARC verdicts. Without it, authentication "
                "cannot be analyzed. Ensure you paste the COMPLETE raw headers "
                "from a received email — not the sent-message headers. "
                "In Gmail: open the email → three-dot menu → 'Show original'."
            ),
            protocol="NONE",
        )

    # ── Case 2: No authentication performed ──────────────────────────────
    if spf.result == "UNKNOWN" and dkim.result == "UNKNOWN":
        domain_note = f" for From domain '{from_domain}'" if from_domain else ""
        return RootCause(
            code=RootCauseCode.NO_AUTHENTICATION,
            title="No Authentication Performed",
            description=(
                f"The receiving mail server did not report any SPF or DKIM "
                f"authentication result{domain_note}. "
                "This typically means no SPF record exists for the sending "
                "domain, the message carried no DKIM signature, or the "
                "Authentication-Results header was added by a server that does "
                "not perform authentication checks. "
                "Without at least one passing and aligned authentication method, "
                "DMARC cannot pass."
            ),
            protocol="NONE",
        )

    # ── Case 3: SPF authentication failure ────────────────────────────────
    if spf.result == "FAIL":
        spf_d = spf.domain or from_domain or "the sending domain"
        raw = f" (raw: spf={spf.raw_result})" if spf.raw_result else ""
        return RootCause(
            code=RootCauseCode.SPF_AUTH_FAIL,
            title="SPF Authentication Failure",
            description=(
                f"The receiving server checked the SPF record for '{spf_d}' "
                f"and determined that the sending IP address is NOT authorized "
                f"to send mail for that domain{raw}. "
                "Either the server's IP is not listed in the SPF record, the "
                "record exceeded the 10 DNS-lookup limit and was voided, or "
                "the sending service was not added to the authorized senders list."
            ),
            protocol="SPF",
        )

    # ── Case 4: DKIM authentication failure ───────────────────────────────
    if dkim.result == "FAIL":
        dkim_d = dkim.domain or from_domain or "the signing domain"
        sel = f" (selector: {dkim.selector})" if dkim.selector else ""
        raw = f" (raw: dkim={dkim.raw_result})" if dkim.raw_result else ""
        return RootCause(
            code=RootCauseCode.DKIM_AUTH_FAIL,
            title="DKIM Signature Verification Failure",
            description=(
                f"The DKIM signature signed by '{dkim_d}'{sel} "
                f"failed cryptographic verification{raw}. "
                "Common causes: the public key in DNS was rotated or deleted "
                "after the message was signed, the message body or headers were "
                "modified in transit (e.g. by a mailing list or forwarder), or "
                "the DKIM DNS record contains an empty or incorrect public key."
            ),
            protocol="DKIM",
        )

    # ── Case 5: Both authenticated but both misaligned ────────────────────
    if alignment.spf is False and alignment.dkim is False:
        spf_d = spf.domain or "unknown"
        dkim_d = dkim.domain or "unknown"
        from_d = from_domain or "unknown"
        return RootCause(
            code=RootCauseCode.BOTH_ALIGNMENT_FAIL,
            title="SPF and DKIM Alignment Failure",
            description=(
                f"Both SPF and DKIM authentication passed, but neither is "
                f"aligned with the From domain ('{from_d}'). "
                f"DMARC requires at least one authenticated domain to match "
                f"the From domain. "
                f"SPF authenticated '{spf_d}' under {alignment.spf_mode} mode. "
                f"DKIM was signed by '{dkim_d}' under {alignment.dkim_mode} mode. "
                "Neither domain shares an organizational domain with the From address."
            ),
            protocol="DMARC",
        )

    # ── Case 6: SPF aligned-fail only (DKIM not available) ────────────────
    if alignment.spf is False and alignment.dkim is None:
        spf_d = spf.domain or "unknown"
        from_d = from_domain or "unknown"
        return RootCause(
            code=RootCauseCode.SPF_ALIGNMENT_FAIL,
            title="SPF Alignment Failure",
            description=(
                f"SPF authentication passed for '{spf_d}', but this domain "
                f"does not align with the From domain ('{from_d}') under "
                f"{alignment.spf_mode} alignment mode. "
                "This occurs when email is sent through a third-party service "
                "(such as an ESP) that uses its own Return-Path domain rather "
                "than yours. Since DKIM did not provide an aligned pass either, "
                "there is no aligned authentication path for DMARC to approve."
            ),
            protocol="SPF",
        )

    # ── Case 7: DKIM aligned-fail only (SPF not available) ────────────────
    if alignment.dkim is False and alignment.spf is None:
        dkim_d = dkim.domain or "unknown"
        from_d = from_domain or "unknown"
        return RootCause(
            code=RootCauseCode.DKIM_ALIGNMENT_FAIL,
            title="DKIM Alignment Failure",
            description=(
                f"The message was signed by DKIM with domain '{dkim_d}', "
                f"but this domain does not align with the From domain "
                f"('{from_d}') under {alignment.dkim_mode} alignment mode. "
                "This typically occurs when your email provider signs messages "
                "using its own infrastructure domain rather than your custom "
                "sending domain. Since SPF did not provide an aligned pass, "
                "DMARC has no passing aligned path."
            ),
            protocol="DKIM",
        )

    # ── Case 8: DMARC explicitly failed (catch-all) ────────────────────────
    if dmarc.result == "FAIL":
        return RootCause(
            code=RootCauseCode.DMARC_POLICY_FAIL,
            title="DMARC Policy Failure",
            description=(
                "The receiving server explicitly reported a DMARC failure. "
                "DMARC fails when neither SPF nor DKIM provides an aligned "
                "authentication path matching the From domain. Verify that at "
                "least one of SPF or DKIM is correctly configured AND that the "
                "authenticated domain aligns with your From address domain."
            ),
            protocol="DMARC",
        )

    # No failure — authentication passed
    return None
