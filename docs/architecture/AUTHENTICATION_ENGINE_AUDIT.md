# Deliverability Diagnostic MVP

## Public modes

- `POST /api/v1/analysis`: DNS configuration readiness. It returns SPF, DKIM,
  and DMARC protocol states plus actionable guidance; it never exposes a
  delivery score.
- `POST /api/v1/analysis/headers`: parses one received email's headers and
  reports message SPF/DKIM/DMARC results, identifier domains, alignment, root
  cause, and remediation.
- `POST /api/v1/analysis/combined`: joins a domain configuration check with a
  received-message diagnostic.

## DKIM semantics

Without an explicit selector, DKIM is `UNKNOWN`, not a warning or a failure.
The API explains how to supply a selector or use header mode. A verified
selector is `CONFIGURED`; a missing/invalid supplied selector is reported
separately.

## Alignment

Header mode reads `From`, `Return-Path`, `DKIM-Signature`, and
`Authentication-Results`. It computes relaxed-domain alignment and treats
overall alignment as successful when a passing SPF or DKIM identity aligns,
which matches DMARC's authentication model.

## Remaining limitations

- Relaxed alignment currently uses a conservative domain/suffix comparison;
  production-scale organizational-domain handling should use a Public Suffix
  List library.
- Headers are parsed but cryptographic DKIM verification is delegated to the
  receiving server's `Authentication-Results` evidence.
