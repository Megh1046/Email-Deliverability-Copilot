# Current State

**Document ID:** CTX-002  
**Version:** 4.0  
**Status:** 🟢 ACTIVE  
**Last Updated:** August 2026

---

## Project Phase

**Phase: Header Analysis Pipeline — Operational**

The primary header analysis pipeline (`HeaderAnalysisPipeline`) is implemented and verified with real email headers. The previous architecture (DNS-only analysis with `IntelligenceOrchestrator`, `RuleEngine`, `AnalysisAggregator`, `ScoreCalculator`) has been replaced by the current header-parsing pipeline. Documentation is being synchronized with the actual implementation.

---

## COMPLETED

### ✅ Core Pipeline — `domains/header_analysis/`

**What exists:** A complete 5-stage email authentication troubleshooter pipeline.

**Where:** `app/backend/domains/header_analysis/`

**How it works:**

| Stage | Module | Function |
|-------|--------|----------|
| 1 — Parse | `parser.py` → `HeaderParser` | Extracts From domain, Return-Path domain, DKIM-Signature domain, all Authentication-Results headers into `ParsedHeaderData` |
| 2 — Validate | `validator.py` → `AuthenticationValidator` | Normalizes raw result strings to `PASS | FAIL | UNKNOWN` |
| 3 — Align | `alignment.py` → `check_alignment()` | Computes RFC 7489 SPF and DKIM alignment (relaxed or strict) |
| 4 — Root Cause | `root_cause.py` → `detect_root_cause()` | 8-case priority decision tree identifying primary failure |
| 5 — Remediate | `remediation.py` → `generate_remediation()` | Produces ordered, actionable `RemediationStep[]` |

**Entry point:** `pipeline.py` → `HeaderAnalysisPipeline.analyze()`

**Test status:** `test_header_analysis.py` contains 2 tests that exercise the pipeline end-to-end. Both exercise real header strings; tests may reference the deprecated `HeaderParser` shim (which delegates to `HeaderAnalysisPipeline`).

---

### ✅ API Endpoints — `domains/header_analysis/api.py`

**Primary endpoint:**
```
POST /api/v1/analysis/headers
```
- Accepts `HeaderAnalysisRequest` with `headers` (string), optional `provider_hint`, `spf_alignment_mode`, `dkim_alignment_mode`
- Returns `HeaderAnalysisResponse`
- Implemented and operational

**Verification endpoint:**
```
POST /api/v1/analysis/headers/verify
```
- Accepts `VerifyRemediationRequest` with `domain` and optional `selector`
- Performs live DNS verification via `DnsVerifier`
- Returns `DnsVerificationResult`
- Implemented and operational

---

### ✅ Authentication Result Extraction

**What exists:** The `HeaderParser` (in `parser.py`) correctly extracts authentication results from RFC 8601 `Authentication-Results` headers.

**Verified behavior:**
- All `Authentication-Results` headers are parsed individually
- The first header (prepended by the final receiving MTA) is used as the primary trusted verdict
- SPF result extracted from `spf=` value; SPF domain from `smtp.mailfrom=` / `envelope-from=`
- DKIM result extracted from `dkim=` value; signing domain from `header.d=`; selector from `header.s=`
- DMARC result extracted from `dmarc=` value
- DKIM-Signature `d=` tag parsed as a fallback signing domain when `header.d=` is absent
- Bug fix BUG-007: DKIM-Signature `d=` uses proper semicolon-delimited tag parsing (not a bare regex)

---

### ✅ Alignment Analysis — `alignment.py`

**What exists:** RFC 7489 compliant SPF and DKIM alignment with relaxed and strict mode support.

**Verified behavior:**
- Relaxed alignment: subdomain of From domain is considered aligned
- Strict alignment: exact match required
- SPF alignment only computed when SPF=PASS and both domains are known
- DKIM alignment only computed when DKIM=PASS and both domains are known
- Overall alignment is True when at least one aligned path exists
- `alignment.spf = None` when SPF did not pass (not `False`)

---

### ✅ Root Cause Engine — `root_cause.py`

**What exists:** An 8-case priority decision tree.

| Priority | Code | Condition |
|----------|------|-----------|
| 1 | `NO_HEADERS` | No Authentication-Results header present |
| 2 | `NO_AUTHENTICATION` | Both SPF and DKIM are UNKNOWN |
| 3 | `SPF_AUTH_FAIL` | SPF = FAIL |
| 4 | `DKIM_AUTH_FAIL` | DKIM = FAIL |
| 5 | `BOTH_ALIGNMENT_FAIL` | Both PASS, both misaligned |
| 6 | `SPF_ALIGNMENT_FAIL` | SPF PASS + misaligned; DKIM not helping |
| 7 | `DKIM_ALIGNMENT_FAIL` | DKIM PASS + misaligned; SPF not helping |
| 8 | `DMARC_POLICY_FAIL` | Explicit dmarc=fail (catch-all) |

Returns `None` when no failure is detected.

Bug fix BUG-006: The original `_diagnose()` method missed SPF authentication failure and had incorrect priority ordering. The current 8-case tree is correct.

---

### ✅ Remediation Engine — `remediation.py` + `domains/remediation/provider_guides.py`

**What exists:** Provider-aware remediation steps for each root cause.

- Each root cause code dispatches to a specific step-generator function
- Steps include `action`, `detail`, `sample_record`, `validation_cmd`
- Provider-specific SPF `include:` directives injected from `PROVIDER_SPF_INCLUDES`
- Provider-specific DKIM setup guides injected from `PROVIDER_DKIM_GUIDES`

**Supported providers for remediation:**
- Google Workspace
- Microsoft 365
- SendGrid
- Mailchimp
- Mailgun
- Amazon SES
- Zendesk

---

### ✅ DNS Verification Subsystem — `domains/dns/`

**What exists:** A full DNS verification stack used by the `/verify` endpoint.

| Module | Class | Purpose |
|--------|-------|---------|
| `resolver.py` | `DNSResolver` | 8 record types (A, AAAA, MX, TXT, NS, CNAME, SOA, DMARC), retry logic, per-request cache |
| `spf_verifier.py` | `SPFValidator` | Parses SPF TXT records, counts lookups, reports issues |
| `dkim_verifier.py` | `DKIMValidator` | Validates DKIM TXT records at a given selector |
| `dmarc_verifier.py` | `DMARCValidator` | Parses DMARC record tags, policy enforcement |
| `provider_detector.py` | `DKIMDiscoveryService` | Fingerprints provider from MX/SPF records; returns candidate selectors |
| `dns_verifier.py` | `DnsVerifier` | Orchestrates the DNS verification pipeline |

---

### ✅ Real-World Validated Test — Simplilearn / Amazon SES

**Test performed:** Real email headers from a Simplilearn marketing email delivered via Amazon SES were analyzed using the header pipeline.

**Headers contained:**
- SPF: `pass` — domain: `mailer.simplilearn.training`
- DKIM: `pass` — domain: `simplilearn.training`
- DMARC: `pass`
- From domain: `simplilearn.training`
- Return-Path domain: `mailer.simplilearn.training`
- Sending infrastructure: Amazon SES

**Observed results:**
- `spf.result = "PASS"`
- `dkim.result = "PASS"`
- `dmarc.result = "PASS"`
- `alignment.spf = true` (relaxed: `mailer.simplilearn.training` aligns with `simplilearn.training`)
- `alignment.dkim = true` (exact match: `simplilearn.training`)
- `alignment.overall = true`
- `provider = {"name": "Amazon SES", "confidence": "MEDIUM"}` (via `provider_hint`)
- `passed = true`
- `root_cause = null`
- `remediation = []`

**Conclusion:** The system correctly analyzed a real-world production email with PASS results across all protocols and alignment checks.

---

## IN PROGRESS

### 🔄 Documentation Synchronization

**Status:** Active (this document is part of the synchronization effort).

The context documentation (`PROJECT_CONTEXT.md`, `CURRENT_STATE.md`, `DECISIONS.md`, `NEXT_TASK.md`, `CHANGELOG.md`) described the previous architecture (`IntelligenceOrchestrator`, `RuleEngine`, DNS-only analysis) rather than the current `HeaderAnalysisPipeline`. All context files are being updated to reflect the actual implementation.

---

## NEEDS IMPROVEMENT

### ⚠️ Provider Detection in Header Analysis Pipeline

**Current state:** Provider detection in the header analysis pipeline depends entirely on `provider_hint` being passed in the API request. If no hint is provided, `provider = null` in the response and remediation is generic.

**What is needed:** Automatic provider detection from header evidence:
- Inspect SPF domain (e.g., `amazonses.com` → Amazon SES)
- Inspect DKIM signing domain
- Inspect `Received:` headers for known infrastructure
- Assign confidence level based on signal strength

**Impact:** Without automatic detection, non-technical users (who won't know to supply `provider_hint`) receive generic rather than provider-specific remediation.

---

### ⚠️ Provider Confidence Level

**Current state:** When `provider_hint` is supplied, confidence is always hardcoded to `"MEDIUM"` in the pipeline. There is no mechanism to validate the hint against actual header evidence.

**What is needed:** Signal-based confidence: `HIGH` when multiple fingerprints match, `MEDIUM` for one match, `LOW` for a hint with no supporting evidence.

---

### ⚠️ Remediation Actionability

**Current state:** Remediation steps are ordered and actionable at a general level. Provider-specific DKIM guides exist in `PROVIDER_DKIM_GUIDES` and are injected when a provider is known.

**What is needed:** More complete step-by-step provider-specific remediation that includes:
- Exact current UI paths for each provider's admin console
- Screenshots or visual references (future)
- Verification commands after each step

**Example gap:** The current system may say "Configure DKIM in your provider's admin panel" and inject a guide. But the guide may not reflect the most current UI for that provider version.

---

### ⚠️ Stale Test Files

Several test files in `app/backend/tests/` reference modules from the previous architecture that no longer exist:

| Test File | References | Status |
|-----------|-----------|--------|
| `test_pipeline.py` | `domains.analysis.api`, `DiagnosticRecommendation`, `DomainDiagnosticResponse`, `ProtocolConfiguration` | ❌ Likely failing — old API |
| `test_aggregator.py` | Old `AnalysisAggregator` | ❌ Likely failing — module removed |
| `test_orchestrator.py` | Old `IntelligenceOrchestrator` | ❌ Likely failing — module removed |
| `test_rule_engine.py` | Old `RuleEngine` | ❌ Likely failing — module removed |
| `test_rule_engine_consistency.py` | Old `RuleEngine` | ❌ Likely failing — module removed |
| `test_header_analysis.py` | `domains.header_analysis.header_parser.HeaderParser` (deprecated shim) | ⚠️ Works but triggers DeprecationWarning |

Tests that should be current:
- `test_dkim.py`, `test_spf.py`, `test_dmarc.py`, `test_dns.py`, `test_dkim_discovery.py`, `test_dkim_aggregator_integration.py` — these test `domains/dns/` components that still exist.
- `test_api.py` — status unclear; depends on which API module it references.

> **Status unclear — requires verification:** A full test run is needed to determine which tests pass. The previous claim of "94 tests passing" was made under the old architecture and does not apply to the current codebase structure.

---

## NOT IMPLEMENTED

### ❌ Frontend

No frontend framework is installed. The `app/frontend/` directory exists as a scaffold, but contains no components, pages, or framework configuration. There is no user interface beyond the Swagger UI at `/docs`.

**Impact:** Users cannot currently paste raw email headers into a UI. They must construct a JSON request manually. This is a significant usability gap.

---

### ❌ Automatic JSON Wrapping for Raw Headers

**Current limitation:** The API endpoint expects a JSON request body. If a user pastes raw email headers directly into the HTTP body (without wrapping them in JSON), the server returns:

```
HTTP 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "json_invalid",
      "msg": "JSON decode error",
      "input": "Delivered-To: user@example.com\n...",
      "ctx": { "error": "Expecting property name enclosed in double quotes: ..." }
    }
  ]
}
```

This is **not an email parsing failure**. It is a request-body formatting error. The headers are valid; they are simply not wrapped in JSON.

**What is needed:** A frontend text area where users paste raw headers. The frontend automatically wraps them as:
```json
{ "headers": "<pasted content>" }
```
before making the POST request. Users should never need to understand JSON.

---

### ❌ Automatic Provider Detection from Headers

Not implemented in the header analysis pipeline. See [NEEDS IMPROVEMENT](#needs-improvement).

---

### ❌ Database / Persistence

No database is configured. Analysis results are not stored between requests.

---

### ❌ Authentication / Authorization

The API is entirely open. No API keys, tokens, or user accounts.

---

### ❌ CI/CD

The `.github/workflows/` directory exists but is empty. No automated testing pipelines.

---

### ❌ AI Assistant Layer

Previously planned as milestone M3A. Not started. No OpenAI or LLM integration exists.

---

### ❌ Reporting Domain

Previously planned as milestone M4. Not started. No PDF or JSON export.

---

## Active Public API

### Primary Endpoint — Header Analysis

```
POST /api/v1/analysis/headers
```

**Request (`HeaderAnalysisRequest`):**
```json
{
  "headers": "Delivered-To: user@example.com\nReceived: ...\nAuthentication-Results: ...",
  "provider_hint": "Amazon SES",
  "spf_alignment_mode": "relaxed",
  "dkim_alignment_mode": "relaxed"
}
```

> ⚠️ `headers` must be a JSON string — raw headers embedded as a string value, not as raw HTTP body content.

**Response (`HeaderAnalysisResponse`):** See `domains/header_analysis/schemas.py` for the complete contract.

Key fields:
- `spf`, `dkim`, `dmarc` — `AuthenticationResult` with `result`, `raw_result`, `domain`, `selector`
- `alignment` — `AlignmentResult` with `spf`, `dkim`, `overall`, `spf_mode`, `dkim_mode`
- `from_domain`, `return_path_domain`, `dkim_signing_domain`
- `authentication_results` — raw header strings
- `evidence` — parsed `AuthEvidence[]` objects
- `root_cause` — `RootCause` with `code`, `title`, `description`, `protocol`
- `remediation` — `RemediationStep[]`
- `provider` — `ProviderInfo` with `name`, `confidence`
- `passed` — `bool`
- `failure_summary` — `str | null`

### Verification Endpoint

```
POST /api/v1/analysis/headers/verify
```

**Request:** `{ "domain": "example.com", "selector": "google" }`

**Response:** `DnsVerificationResult` — live DNS verification results.

---

## Project Health (Actual)

| Area | Status | Notes |
|------|--------|-------|
| Header Analysis Pipeline | 🟢 Implemented | 5-stage pipeline operational |
| API Endpoints | 🟢 Implemented | `/headers` and `/headers/verify` active |
| Authentication Extraction | 🟢 Implemented | RFC 8601 parsing with multi-hop support |
| Alignment Analysis | 🟢 Implemented | RFC 7489 relaxed/strict |
| Root Cause Engine | 🟢 Implemented | 8-case decision tree |
| Remediation Engine | 🟢 Implemented | Provider-aware, all 8 root causes covered |
| DNS Verification | 🟢 Implemented | Used by verify endpoint |
| Real Email Validation | 🟢 Verified | Simplilearn/Amazon SES test passed |
| Provider Detection (pipeline) | 🟡 Manual only | Requires `provider_hint`; no auto-detection |
| Frontend | 🔴 Not started | No framework, no components |
| Test Suite | 🔴 Stale | Many tests reference removed modules |
| Database | 🔴 Not started | No persistence |
| CI/CD | 🔴 Not started | Empty workflows |
| Documentation | 🟡 Updating | Being synchronized with current code |
