"""
Remediation engine.

Generates ordered, human-readable, actionable remediation steps
based on the root cause code detected by root_cause.py.

Provider-specific step-by-step guides are included for the major
email sending platforms (migrated from the old RecommendationMapper).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .schemas import AuthenticationResult, RemediationStep
from .root_cause import RootCauseCode
from domains.remediation.provider_guides import PROVIDER_DKIM_GUIDES, PROVIDER_SPF_INCLUDES

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _spf_include(provider: Optional[str]) -> str:
    return PROVIDER_SPF_INCLUDES.get(provider or "", "include:<your-provider-spf>")


def _dkim_guide_detail(provider: Optional[str]) -> Optional[str]:
    guide = PROVIDER_DKIM_GUIDES.get(provider or "")
    if not guide:
        return None
    return "\n".join(f"{i + 1}. {s}" for i, s in enumerate(guide))


# ---------------------------------------------------------------------------
# Remediation generators per root cause
# ---------------------------------------------------------------------------

def _steps_no_headers() -> List[RemediationStep]:
    return [
        RemediationStep(
            step=1,
            action="Retrieve the full raw email headers from the failed message.",
            detail=(
                "In Gmail: open the email → click the three-dot menu (⋮) → "
                "'Show original'. In Outlook: open the email → File → Properties → "
                "Internet headers. In Apple Mail: View → Message → All Headers."
            ),
        ),
        RemediationStep(
            step=2,
            action="Copy ALL headers, including Authentication-Results, Received, DKIM-Signature, and From.",
            detail=(
                "Do not paste only a portion of the headers. The "
                "Authentication-Results header is required to determine "
                "whether SPF, DKIM, and DMARC passed or failed."
            ),
        ),
        RemediationStep(step=3, action="Paste the complete headers back into the analyzer and resubmit."),
    ]


def _steps_no_authentication(domain: str, provider: Optional[str]) -> List[RemediationStep]:
    spf_inc = _spf_include(provider)
    provider_note = f" (detected provider: {provider})" if provider else ""
    return [
        RemediationStep(
            step=1,
            action=f"Publish an SPF TXT record for {domain}{provider_note}.",
            detail="An SPF record tells receiving servers which IPs are authorized to send mail for your domain.",
            sample_record=f"v=spf1 {spf_inc} ~all",
            validation_cmd=f"dig TXT {domain}",
        ),
        RemediationStep(
            step=2,
            action=f"Configure DKIM signing for {domain}.",
            detail=(
                _dkim_guide_detail(provider)
                or "Log in to your email provider's admin panel and follow their DKIM setup instructions to generate and publish a key pair."
            ),
        ),
        RemediationStep(
            step=3,
            action=f"Publish a DMARC record at _dmarc.{domain} to monitor and protect your domain.",
            detail="Start with p=none to monitor without blocking, then escalate after reviewing reports.",
            sample_record=f"v=DMARC1; p=none; rua=mailto:dmarc@{domain}",
            validation_cmd=f"dig TXT _dmarc.{domain}",
        ),
        RemediationStep(
            step=4,
            action="Send a test email and re-analyze the headers to confirm SPF and DKIM pass.",
        ),
    ]


def _steps_spf_auth_fail(
    domain: str,
    spf: AuthenticationResult,
    provider: Optional[str],
) -> List[RemediationStep]:
    spf_d = spf.domain or domain
    spf_inc = _spf_include(provider)
    provider_note = f" (detected provider: {provider})" if provider else ""
    return [
        RemediationStep(
            step=1,
            action=f"Check your current SPF record for {spf_d}.",
            detail="The sending IP is not listed as an authorized sender for this domain.",
            validation_cmd=f"dig TXT {spf_d}",
        ),
        RemediationStep(
            step=2,
            action="Identify the IP address of the mail server that sent this email.",
            detail=(
                "Look at the topmost 'Received:' header to find the originating IP. "
                "Check if that IP belongs to your email provider's infrastructure."
            ),
        ),
        RemediationStep(
            step=3,
            action=f"Add your email provider's sending servers to the SPF record{provider_note}.",
            detail=f"Include the provider's SPF include directive in your SPF record.",
            sample_record=f"v=spf1 {spf_inc} ~all",
        ),
        RemediationStep(
            step=4,
            action=f"Update the TXT record at {spf_d} in your DNS provider with the corrected SPF value.",
            validation_cmd=f"dig TXT {spf_d}",
        ),
        RemediationStep(
            step=5,
            action="Send a test email and verify spf=pass appears in the Authentication-Results header.",
        ),
    ]


def _steps_dkim_auth_fail(
    domain: str,
    dkim: AuthenticationResult,
    provider: Optional[str],
) -> List[RemediationStep]:
    dkim_d = dkim.domain or domain
    selector = dkim.selector or "<selector>"
    guide = _dkim_guide_detail(provider)
    steps = [
        RemediationStep(
            step=1,
            action=f"Verify the DKIM public key record exists in DNS for selector '{selector}'.",
            detail=f"Look up the TXT record at {selector}._domainkey.{dkim_d}.",
            validation_cmd=f"dig TXT {selector}._domainkey.{dkim_d}",
        ),
        RemediationStep(
            step=2,
            action="Check whether the DKIM key was recently rotated or deleted.",
            detail=(
                "If your email provider rotated keys, the signing private key "
                "may no longer match the public key in DNS. Regenerate and "
                "re-publish the DKIM record."
            ),
        ),
        RemediationStep(
            step=3,
            action="Confirm the DKIM record is not revoked (p= must not be empty).",
            detail="A record with 'p=' (empty public key) is a revoked key. If so, generate a new key pair.",
        ),
    ]
    if guide:
        steps.append(RemediationStep(
            step=4,
            action=f"Re-configure DKIM signing in {provider} using the official setup guide.",
            detail=guide,
        ))
    else:
        steps.append(RemediationStep(
            step=4,
            action="Regenerate the DKIM key pair in your email provider's admin panel and re-publish the DNS TXT record.",
        ))
    steps.append(RemediationStep(
        step=len(steps) + 1,
        action="After updating DNS, wait 15–60 minutes for propagation, then send a test email.",
    ))
    return steps


def _steps_spf_alignment_fail(
    domain: str,
    spf: AuthenticationResult,
    provider: Optional[str],
) -> List[RemediationStep]:
    spf_d = spf.domain or "unknown"
    spf_inc = _spf_include(provider)
    return [
        RemediationStep(
            step=1,
            action=f"Understand the problem: SPF passed for '{spf_d}', not '{domain}'.",
            detail=(
                "SPF alignment requires the Return-Path (envelope-from) domain "
                "to match the From domain. Your messages are being routed through "
                "a service that uses its own Return-Path domain."
            ),
        ),
        RemediationStep(
            step=2,
            action=f"Configure a custom Return-Path / Bounce domain that uses {domain}.",
            detail=(
                "Most email providers (SendGrid, Mailchimp, etc.) support "
                "setting a custom bounce domain. This makes the envelope-from "
                "address use your domain instead of theirs."
            ),
        ),
        RemediationStep(
            step=3,
            action=f"Publish an SPF record for {domain} authorizing your email provider.",
            sample_record=f"v=spf1 {spf_inc} ~all",
            validation_cmd=f"dig TXT {domain}",
        ),
        RemediationStep(
            step=4,
            action="Alternatively — configure DKIM alignment instead.",
            detail=(
                "DMARC passes when EITHER SPF or DKIM is aligned. "
                "If you configure DKIM to sign with your From domain, "
                "SPF alignment is less critical."
            ),
        ),
    ]


def _steps_dkim_alignment_fail(
    domain: str,
    dkim: AuthenticationResult,
    provider: Optional[str],
) -> List[RemediationStep]:
    dkim_d = dkim.domain or "unknown"
    guide = _dkim_guide_detail(provider)
    steps = [
        RemediationStep(
            step=1,
            action=f"Understand the problem: DKIM was signed by '{dkim_d}', not '{domain}'.",
            detail=(
                "DKIM alignment requires the d= signing domain to match "
                "the From domain. Your provider is signing with its own domain "
                "instead of yours."
            ),
        ),
        RemediationStep(
            step=2,
            action=f"Configure your email provider to sign outbound messages using '{domain}'.",
            detail="This feature is typically called 'Custom DKIM Domain', 'Sender Authentication', or 'Domain Authentication'.",
        ),
    ]
    if guide:
        steps.append(RemediationStep(
            step=3,
            action=f"Follow the {provider} domain authentication guide.",
            detail=guide,
        ))
    else:
        steps.append(RemediationStep(
            step=3,
            action="Check your email provider's documentation for 'custom DKIM domain' or 'sender authentication'.",
        ))
    steps.append(RemediationStep(
        step=len(steps) + 1,
        action="After reconfiguring, send a test email and confirm the DKIM signing domain matches your From domain.",
    ))
    return steps


def _steps_both_alignment_fail(
    domain: str,
    spf: AuthenticationResult,
    dkim: AuthenticationResult,
    provider: Optional[str],
) -> List[RemediationStep]:
    guide = _dkim_guide_detail(provider)
    spf_inc = _spf_include(provider)
    steps = [
        RemediationStep(
            step=1,
            action="Understand the problem: both SPF and DKIM passed but neither is aligned with the From domain.",
            detail=(
                f"From domain: {domain}. "
                f"SPF domain: {spf.domain or 'unknown'}. "
                f"DKIM domain: {dkim.domain or 'unknown'}. "
                "DMARC requires at least one to match."
            ),
        ),
        RemediationStep(
            step=2,
            action=f"Fix DKIM alignment first: configure your email provider to sign with '{domain}'.",
            detail=guide or "Find the DKIM or sender authentication settings in your email provider's admin panel.",
        ),
        RemediationStep(
            step=3,
            action=f"Fix SPF alignment: set the Return-Path / bounce domain to '{domain}' and publish an SPF record.",
            sample_record=f"v=spf1 {spf_inc} ~all",
            validation_cmd=f"dig TXT {domain}",
        ),
        RemediationStep(
            step=4,
            action="Send a test email and verify at least one of SPF or DKIM shows as aligned.",
        ),
    ]
    return steps


def _steps_dmarc_policy_fail(domain: str) -> List[RemediationStep]:
    return [
        RemediationStep(
            step=1,
            action=f"Verify your SPF record for {domain} is correct and authorizes the sending server.",
            validation_cmd=f"dig TXT {domain}",
        ),
        RemediationStep(
            step=2,
            action="Verify your DKIM record is published and matches the private key used for signing.",
            validation_cmd=f"dig TXT <selector>._domainkey.{domain}",
        ),
        RemediationStep(
            step=3,
            action="Confirm at least one of SPF or DKIM is aligned with your From domain.",
            detail=(
                "DMARC passes when the From domain matches EITHER the "
                "SPF-authenticated envelope-from domain OR the DKIM signing domain."
            ),
        ),
        RemediationStep(
            step=4,
            action="Send a test email after correcting the issues, then re-analyze the headers.",
        ),
    ]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_remediation(
    root_cause_code: Optional[str],
    from_domain: Optional[str],
    spf: AuthenticationResult,
    dkim: AuthenticationResult,
    provider_name: Optional[str] = None,
) -> List[RemediationStep]:
    """
    Generate ordered remediation steps for the detected root cause.

    Args:
        root_cause_code: Code string from RootCauseCode (or None if no failure).
        from_domain:     RFC 5322 From header domain.
        spf:             Normalized SPF result.
        dkim:            Normalized DKIM result.
        provider_name:   Detected email provider name, used for provider-specific guidance.

    Returns:
        List of RemediationStep objects, empty when there is no failure.
    """
    if not root_cause_code:
        return []

    domain = from_domain or "yourdomain.com"

    dispatch = {
        RootCauseCode.NO_HEADERS: lambda: _steps_no_headers(),
        RootCauseCode.NO_AUTHENTICATION: lambda: _steps_no_authentication(domain, provider_name),
        RootCauseCode.SPF_AUTH_FAIL: lambda: _steps_spf_auth_fail(domain, spf, provider_name),
        RootCauseCode.DKIM_AUTH_FAIL: lambda: _steps_dkim_auth_fail(domain, dkim, provider_name),
        RootCauseCode.SPF_ALIGNMENT_FAIL: lambda: _steps_spf_alignment_fail(domain, spf, provider_name),
        RootCauseCode.DKIM_ALIGNMENT_FAIL: lambda: _steps_dkim_alignment_fail(domain, dkim, provider_name),
        RootCauseCode.BOTH_ALIGNMENT_FAIL: lambda: _steps_both_alignment_fail(domain, spf, dkim, provider_name),
        RootCauseCode.DMARC_POLICY_FAIL: lambda: _steps_dmarc_policy_fail(domain),
    }

    handler = dispatch.get(root_cause_code)
    return handler() if handler else []
