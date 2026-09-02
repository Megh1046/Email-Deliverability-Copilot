# Project Context

**Document ID:** CTX-001  
**Version:** 3.0  
**Status:** 🟢 ACTIVE  
**Last Updated:** August 2026

---

## 1. Project Name

**Email Deliverability Copilot**

---

## 2. Project Purpose

An email authentication troubleshooter that allows users to paste raw email headers and receive a plain-English diagnosis of SPF, DKIM, and DMARC authentication failures, along with actionable remediation steps. Designed for non-technical users — particularly marketing executives — who need to understand and fix deliverability problems without requiring DNS or infrastructure expertise.

---

## 3. Problem Statement

Marketing teams own deliverability outcomes but rarely own DNS infrastructure. When an email campaign fails authentication, the error messages are technical and opaque. The people who care most about fixing the problem cannot interpret the signals. This gap causes campaigns to fail silently, emails to land in spam, and revenue to be lost.

---

## 4. Target Users

| Priority | User | Key Need |
|----------|------|----------|
| Primary | Marketing Executives | Diagnose deliverability issues without DNS knowledge |
| Secondary | CRM / Marketing Ops Admins | Guided authentication setup |
| Secondary | IT / DNS Administrators | Record verification and remediation guidance |
| Secondary | Digital Marketing Agencies | Multi-domain diagnostics |

---

## 5. Core Workflow

The intended end-to-end user experience:

```
User pastes raw email headers
        ↓
Frontend wraps headers in JSON request body
        ↓
POST /api/v1/analysis/headers
        ↓
HeaderAnalysisPipeline.analyze()
        ↓
Stage 1 — Parse: HeaderParser extracts From domain, Return-Path domain,
          DKIM-Signature domain, all Authentication-Results headers
        ↓
Stage 2 — Validate: AuthenticationValidator normalizes
          raw results → PASS | FAIL | UNKNOWN
        ↓
Stage 3 — Align: check_alignment computes SPF and DKIM alignment
          per RFC 7489 (relaxed or strict mode)
        ↓
Stage 4 — Root Cause: detect_root_cause identifies the primary failure
        ↓
Stage 5 — Remediate: generate_remediation produces ordered fix steps
        ↓
HeaderAnalysisResponse returned to frontend
        ↓
Frontend presents plain-English results to user
```

---

## 6. Current Architecture

The backend is organized as a **domain-oriented FastAPI application** with two active domain groups:

### `domains/header_analysis/` — Primary Pipeline (ACTIVE)

This is the core feature. It handles real email header parsing and produces the primary API response.

```
app/backend/
├── main.py                          # FastAPI app — registers analysis router at /api/v1
├── requirements.txt                 # fastapi, uvicorn, pydantic, dnspython, httpx, pytest
├── shared/
│   └── models.py                    # AnalysisIssue, DomainRequest, FullAnalysisRequest, BaseApiResponse
├── domains/
│   ├── header_analysis/             # PRIMARY PIPELINE
│   │   ├── __init__.py              # Exposes HeaderAnalysisPipeline, HeaderAnalysisResponse
│   │   ├── api.py                   # API router — POST /analysis/headers, POST /analysis/headers/verify
│   │   ├── pipeline.py              # HeaderAnalysisPipeline — 5-stage orchestrator
│   │   ├── parser.py                # HeaderParser — extracts evidence from raw headers
│   │   ├── validator.py             # AuthenticationValidator — normalizes to PASS|FAIL|UNKNOWN
│   │   ├── alignment.py             # check_alignment() — RFC 7489 relaxed/strict alignment
│   │   ├── root_cause.py            # detect_root_cause() — 8-case decision tree
│   │   ├── remediation.py           # generate_remediation() — ordered fix steps
│   │   ├── schemas.py               # All response types for the pipeline
│   │   └── header_parser.py         # ⚠️ DEPRECATED shim — do not use directly
│   ├── dns/                         # DNS VERIFICATION (secondary, used by verify endpoint)
│   │   ├── resolver.py              # DNSResolver — 8 record types, retry logic, cache
│   │   ├── spf_verifier.py          # SPFValidator — parses and validates SPF records
│   │   ├── dkim_verifier.py         # DKIMValidator — validates DKIM DNS TXT records
│   │   ├── dmarc_verifier.py        # DMARCValidator — parses and validates DMARC records
│   │   ├── provider_detector.py     # DKIMDiscoveryService — provider fingerprinting
│   │   ├── dns_verifier.py          # DnsVerifier — orchestrates DNS verification
│   │   └── schemas.py               # DNS domain schemas: SpfResult, DkimResult, DmarcResult, DnsVerificationResult
│   ├── remediation/
│   │   └── provider_guides.py       # PROVIDER_DKIM_GUIDES, PROVIDER_SPF_INCLUDES
│   └── shared/
│       └── constants.py             # UNKNOWN_SELECTOR and other shared constants
└── tests/
    ├── test_header_analysis.py      # Pipeline integration tests
    ├── test_pipeline.py             # ⚠️ References old domains/analysis API — may be stale
    ├── test_api.py
    ├── test_dkim.py
    ├── test_dmarc.py
    ├── test_dns.py
    ├── test_spf.py
    ├── test_aggregator.py           # Tests old AnalysisAggregator — may be stale
    ├── test_orchestrator.py         # Tests old IntelligenceOrchestrator — may be stale
    ├── test_rule_engine.py          # Tests old RuleEngine — may be stale
    └── test_rule_engine_consistency.py
```

> **⚠️ Note on Old Architecture Modules:** Several test files reference modules from the previous architecture (`domains/analysis/`, `core/orchestrator.py`, `domains/rules/`). Those modules no longer exist in the current codebase. These tests may be stale or failing. See [CURRENT_STATE.md](CURRENT_STATE.md) for test status details.

---

## 7. Backend Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI ≥ 0.111.0 |
| Runtime | Python 3.11+ |
| Data validation | Pydantic ≥ 2.7.0 |
| DNS lookups | dnspython ≥ 2.6.1 |
| HTTP client | httpx ≥ 0.27.0 |
| ASGI server | uvicorn[standard] ≥ 0.30.0 |
| Tests | pytest ≥ 8.2.0, pytest-asyncio ≥ 0.23.0 |

---

## 8. Frontend Stack

> **Status: Not implemented.** No frontend framework is installed. There is a `frontend/` directory scaffold, but no components, pages, or framework configuration exist. The API is currently accessible only via direct HTTP calls (e.g., Swagger UI at `/docs`).

---

## 9. API Endpoints

### Primary Endpoint

```
POST /api/v1/analysis/headers
```

**Purpose:** Parse raw email headers, diagnose authentication failures, return remediation steps.

**Request body (JSON):**
```json
{
  "headers": "<raw email header string>",
  "provider_hint": "Amazon SES",
  "spf_alignment_mode": "relaxed",
  "dkim_alignment_mode": "relaxed"
}
```

- `headers` — The complete raw email header block as a plain string. **Required.**
- `provider_hint` — Optional. Name of the known sending provider. Used to select provider-specific remediation. Defaults to `null`.
- `spf_alignment_mode` — `"relaxed"` (default) or `"strict"`.
- `dkim_alignment_mode` — `"relaxed"` (default) or `"strict"`.

> **⚠️ IMPORTANT — UX Distinction:** The `headers` field must be a JSON string (the raw email headers embedded inside a JSON key-value pair). Pasting raw headers directly as the HTTP request body will return `HTTP 422 Unprocessable Entity` with `json_invalid`. The eventual user-facing experience will have a frontend text area that wraps input automatically. See [Known Limitations](#18-known-limitations).

**Response body (`HeaderAnalysisResponse`):**
```json
{
  "spf": { "result": "PASS", "raw_result": "pass", "domain": "mailer.simplilearn.training" },
  "dkim": { "result": "PASS", "raw_result": "pass", "domain": "simplilearn.training", "selector": "..." },
  "dmarc": { "result": "PASS", "raw_result": "pass" },
  "alignment": {
    "spf": true,
    "dkim": true,
    "overall": true,
    "spf_mode": "relaxed",
    "dkim_mode": "relaxed"
  },
  "from_domain": "simplilearn.training",
  "return_path_domain": "mailer.simplilearn.training",
  "dkim_signing_domain": "simplilearn.training",
  "authentication_results": ["...raw header string..."],
  "evidence": [...],
  "root_cause": null,
  "remediation": [],
  "provider": { "name": "Amazon SES", "confidence": "MEDIUM" },
  "passed": true,
  "failure_summary": null
}
```

### Verification Endpoint

```
POST /api/v1/analysis/headers/verify
```

**Purpose:** Perform a live DNS check on a domain's SPF, DKIM, and DMARC records to confirm remediation was applied.

**Request body:**
```json
{
  "domain": "example.com",
  "selector": "google"
}
```

**Response:** `DnsVerificationResult` — full DNS analysis with `SpfResult`, `DkimResult`, `DmarcResult`.

### Root Endpoint

```
GET /
```

Returns: `{"message": "Email Deliverability Copilot backend is running"}`

---

## 10. Data Flow (Current Implementation)

```
Raw email headers (string)
        │
        ▼
HeaderParser.parse()
  ├── Python email.parser.Parser parses raw headers
  ├── Extracts From: → from_domain
  ├── Extracts Return-Path: → return_path_domain
  ├── Extracts ALL Authentication-Results headers → all_evidence[]
  │   └── First header = primary_evidence (most trusted MTA verdict)
  ├── Parses each Authentication-Results per RFC 8601:
  │   ├── spf_result, spf_domain (smtp.mailfrom)
  │   ├── dkim_result, dkim_domain (header.d=), dkim_selector (header.s=)
  │   └── dmarc_result
  └── Extracts DKIM-Signature d= → dkim_signature_domain (fallback)
        │
        ▼
AuthenticationValidator.validate()
  ├── SPF: pass→PASS  fail/softfail→FAIL  all others→UNKNOWN
  ├── DKIM: pass→PASS  fail/policy/permerror→FAIL  all others→UNKNOWN
  └── DMARC: pass→PASS  fail/reject→FAIL  all others→UNKNOWN
        │
        ▼
check_alignment()
  ├── SPF alignment: only if SPF=PASS and from_domain and spf.domain known
  │   relaxed: subdomain match (e.g. mailer.example.com aligns with example.com)
  │   strict:  exact match only
  ├── DKIM alignment: only if DKIM=PASS and from_domain and dkim.domain known
  │   relaxed: subdomain match
  │   strict:  exact match only
  └── overall: True if any aligned path exists; False if all fail; None if no data
        │
        ▼
detect_root_cause()
  8-case priority decision tree:
  1. NO_HEADERS          — No Authentication-Results header present
  2. NO_AUTHENTICATION   — Both SPF and DKIM are UNKNOWN
  3. SPF_AUTH_FAIL       — SPF=FAIL (spf=fail or spf=softfail)
  4. DKIM_AUTH_FAIL      — DKIM=FAIL
  5. BOTH_ALIGNMENT_FAIL — Both PASS but both misaligned
  6. SPF_ALIGNMENT_FAIL  — SPF PASS + misaligned; DKIM not available
  7. DKIM_ALIGNMENT_FAIL — DKIM PASS + misaligned; SPF not available
  8. DMARC_POLICY_FAIL   — Explicit dmarc=fail (catch-all)
  → Returns None if no failure found
        │
        ▼
generate_remediation()
  ├── Dispatches to a specific step-generator based on root_cause_code
  ├── Each generator produces ordered RemediationStep[] list
  ├── Provider-specific content is injected from:
  │   ├── PROVIDER_DKIM_GUIDES (domains/remediation/provider_guides.py)
  │   └── PROVIDER_SPF_INCLUDES (domains/remediation/provider_guides.py)
  └── Supported providers: Google Workspace, Microsoft 365, SendGrid,
      Mailchimp, Mailgun, Amazon SES, Zendesk
        │
        ▼
HeaderAnalysisResponse
  ├── spf, dkim, dmarc (AuthenticationResult)
  ├── alignment (AlignmentResult: spf, dkim, overall, modes)
  ├── from_domain, return_path_domain, dkim_signing_domain
  ├── authentication_results (raw strings), evidence (AuthEvidence[])
  ├── root_cause (RootCause | null)
  ├── remediation (RemediationStep[])
  ├── provider (ProviderInfo | null)
  ├── passed (bool)
  └── failure_summary (str | null)
```

---

## 11. Authentication Analysis

### SPF

The system reads the `spf=` value from the `Authentication-Results` header.

| Raw value | Normalized |
|-----------|-----------|
| `pass` | `PASS` |
| `fail` | `FAIL` |
| `softfail` | `FAIL` |
| `neutral`, `none`, `temperror`, `permerror` | `UNKNOWN` |

SPF authenticated domain is taken from `smtp.mailfrom=` or `envelope-from=` in the Authentication-Results header, falling back to the Return-Path domain from the raw headers.

### DKIM

The system reads the `dkim=` value from the `Authentication-Results` header.

| Raw value | Normalized |
|-----------|-----------|
| `pass` | `PASS` |
| `fail` | `FAIL` |
| `policy` | `FAIL` |
| `permerror` | `FAIL` |
| `neutral`, `none`, `temperror` | `UNKNOWN` |

DKIM signing domain is taken from `header.d=` in the Authentication-Results header, falling back to the `d=` tag in the `DKIM-Signature` raw header. Selector is taken from `header.s=`.

### DMARC

The system reads the `dmarc=` value from the `Authentication-Results` header.

| Raw value | Normalized |
|-----------|-----------|
| `pass` | `PASS` |
| `fail` | `FAIL` |
| `reject` | `FAIL` |
| `none`, `temperror`, `permerror` | `UNKNOWN` |

---

## 12. Alignment Analysis

Alignment is distinct from authentication. Authentication asks: *"Is this domain's identity verified?"* Alignment asks: *"Does the verified domain match the visible From address?"*

### Relaxed Alignment (default)

Organizational-domain matching. A subdomain of the From domain is considered aligned.

| From domain | Authenticated domain | Aligned? |
|------------|---------------------|---------|
| `example.com` | `example.com` | ✅ Yes |
| `example.com` | `mail.example.com` | ✅ Yes |
| `example.com` | `bounce.example.com` | ✅ Yes |
| `example.com` | `sendgrid.net` | ❌ No |

### Strict Alignment

Exact match required.

| From domain | Authenticated domain | Aligned? |
|------------|---------------------|---------|
| `example.com` | `example.com` | ✅ Yes |
| `example.com` | `mail.example.com` | ❌ No |
| `example.com` | `bounce.example.com` | ❌ No |

### Key Rule

**Alignment is only computed when the relevant authentication result is PASS.** If SPF=FAIL, SPF alignment is `null` (not applicable), not `false`. DMARC passes when **at least one** of SPF or DKIM is both authenticated (PASS) and aligned.

---

## 13. Provider Detection

Provider detection in the header analysis pipeline works as follows:

- If `provider_hint` is supplied in the API request, it is used directly with `confidence = "MEDIUM"`.
- If no hint is supplied, `provider = null` in the response.

The `DKIMDiscoveryService` (used by the DNS verification endpoint) performs fingerprint-based provider detection from live DNS records:

| Provider | MX fingerprint | SPF fingerprint | DKIM selectors |
|----------|---------------|----------------|----------------|
| Google Workspace | `aspmx.l.google.com` | `_spf.google.com` | `google` |
| Microsoft 365 | `mail.protection.outlook.com` | `spf.protection.outlook.com` | `selector1`, `selector2` |
| SendGrid | `mx.sendgrid.net` | `sendgrid.net` | `s1`, `s2` |
| Mailchimp | *(none)* | `servers.mcsv.net`, `spf.mandrillapp.com` | `k1`, `k2`, `k3` |
| Mailgun | `mxa.mailgun.org` | `mailgun.org` | `pic`, `krs`, `mg`, `mailo` |
| Zendesk | *(none)* | `mail.zendesk.com` | `zendesk1`, `zendesk2` |
| Amazon SES | `smtp.receptor.amazon.com`, `inbound-smtp.amazonaws.com` | `amazonses.com` | *(random 32-char selectors)* |

> **Note:** Provider detection in the header analysis pipeline is limited to what is passed via `provider_hint`. Automatic provider detection from headers alone (e.g., inferring "Amazon SES" from the presence of `amazonses.com` in the SPF domain) is **not yet implemented** in the pipeline. This is an improvement area.

---

## 14. Root-Cause Engine

Eight distinct root cause codes are defined in `RootCauseCode` (`root_cause.py`):

| Code | Title | Protocol |
|------|-------|---------|
| `NO_HEADERS` | No Authentication Results Found | NONE |
| `NO_AUTHENTICATION` | No Authentication Performed | NONE |
| `SPF_AUTH_FAIL` | SPF Authentication Failure | SPF |
| `DKIM_AUTH_FAIL` | DKIM Signature Verification Failure | DKIM |
| `BOTH_ALIGNMENT_FAIL` | SPF and DKIM Alignment Failure | DMARC |
| `SPF_ALIGNMENT_FAIL` | SPF Alignment Failure | SPF |
| `DKIM_ALIGNMENT_FAIL` | DKIM Alignment Failure | DKIM |
| `DMARC_POLICY_FAIL` | DMARC Policy Failure | DMARC |

Each `RootCause` object carries a `code`, `title`, `description` (full explanation), and `protocol`.

When no failure is detected, `root_cause = null` and `remediation = []`.

---

## 15. Remediation System

### Current State

Remediation steps are generated per root cause code. Steps are ordered and include:
- `action` — Short headline instruction
- `detail` — Longer explanation or sub-steps
- `sample_record` — Example DNS record value (where applicable)
- `validation_cmd` — Shell command to verify the fix (e.g., `dig TXT example.com`)

Provider-specific content is injected when `provider_name` is known:
- **SPF:** Provider-specific `include:` mechanism inserted into sample records
- **DKIM:** Provider-specific step-by-step setup guide injected into remediation steps

Provider guides exist for: Google Workspace, Microsoft 365, SendGrid, Mailchimp, Mailgun, Amazon SES, Zendesk.

### Current Limitation

The current remediation includes provider-specific DKIM setup steps and SPF include directives. However, the provider must be explicitly supplied via `provider_hint` in the API request; the pipeline does not detect providers automatically from headers.

Provider guides cover the sequence of admin UI steps (log in, navigate to settings, copy DNS records, publish, verify), but confidence level is always `"MEDIUM"` because the system cannot independently verify that the hint is correct.

### Improvement Needed

For a fully non-technical user experience, the system needs:
1. Automatic provider detection from header evidence (e.g., reading SPF domain, DKIM signing domain, Received headers)
2. Confidence levels derived from actual signal matching (HIGH, MEDIUM, LOW)
3. Provider-specific step-by-step remediation with accurate UI paths for the current version of each provider's admin console

---

## 16. Testing Status

See [CURRENT_STATE.md](CURRENT_STATE.md) for full test details.

The header analysis pipeline has been validated with a real-world Simplilearn email sent through Amazon SES.

---

## 17. Known Limitations

1. **No frontend UI.** All interaction is currently via the Swagger UI (`/docs`) or direct HTTP requests.
2. **Raw headers require JSON wrapping.** Pasting raw headers directly as the request body returns HTTP 422. The `headers` field must be a JSON string.
3. **Provider detection is manual.** The pipeline does not automatically detect the sending provider from headers. `provider_hint` must be set by the caller.
4. **Provider confidence is always MEDIUM.** When `provider_hint` is used, confidence is hardcoded to `"MEDIUM"` since the system cannot verify the hint.
5. **Remediation is generic when no provider is supplied.** Without `provider_hint`, remediation steps are protocol-specific but not provider-specific.
6. **Several test files reference the old architecture** (`domains/analysis/`, `core/orchestrator.py`, `domains/rules/`). These tests may not pass against the current codebase.
7. **No database.** Analysis results are not persisted.
8. **No authentication/authorization.** The API is open.
9. **No CI/CD.** The `.github/workflows/` directory exists but is empty.

---

## 18. Current Priorities

See [NEXT_TASK.md](NEXT_TASK.md) for the detailed task list.

| Priority | Task |
|----------|------|
| P0 | Documentation synchronization (this task) |
| P1 | User-friendly raw-header input (frontend text area → JSON wrapping) |
| P2 | Automatic provider detection from header evidence |
| P3 | Provider-specific actionable remediation |
| P4 | Frontend result presentation |
| P5 | Testing — fix stale tests, add pipeline coverage |
| P6 | Production hardening (CI/CD, error handling) |

---

## 19. Deprecated / Outdated Architecture

The following architecture described in earlier versions of this document **no longer exists** in the codebase:

| Old Component | Old Location | Status |
|--------------|-------------|--------|
| `IntelligenceOrchestrator` | `core/orchestrator.py` | ❌ Removed — replaced by `HeaderAnalysisPipeline` |
| `AnalysisAggregator` | `domains/analysis/aggregator/` | ❌ Removed |
| `RuleEngine` | `domains/rules/engine.py` | ❌ Removed |
| `ScoreCalculator` | `domains/rules/score_calculator.py` | ❌ Removed |
| `BusinessTranslator` | `domains/rules/business_translator.py` | ❌ Removed |
| `RecommendationMapper` | `domains/rules/recommendation_mapper.py` | ❌ Removed |
| `RuleEngineResponse` | `domains/rules/schemas.py` | ❌ Removed |
| `AggregatedAnalysisResponse` | `domains/analysis/aggregator/` | ❌ Removed |
| `POST /api/v1/analysis` (domain-based) | `domains/analysis/api.py` | ❌ Replaced by `POST /api/v1/analysis/headers` |
| `POST /api/v1/analysis/dns` etc. | granular DNS endpoints | ❌ Removed |
| `DeliverabilityScore` (1–100 scoring) | old rule engine | ❌ Removed |
| ARCH-010 through ARCH-016 (old decisions) | `DECISIONS.md` | ⚠️ Partially obsolete — see DECISIONS.md |

The `DKIMDiscoveryService`, `DNSResolver`, `SPFValidator`, `DKIMValidator`, `DMARCValidator` **still exist** in `domains/dns/` and are used by the `POST /api/v1/analysis/headers/verify` endpoint. They are no longer used by the primary header analysis pipeline.

---

## 20. Engineering Philosophy

- **Documentation-Driven Development** — Docs written before code; docs are the source of truth.
- **Domain-Oriented Design** — Business capabilities isolated into domains.
- **Clean, stateless pipeline** — The `HeaderAnalysisPipeline` holds no mutable state and is safe to share across requests.
- **Separation of concerns** — Parsing, validation, alignment, root cause, and remediation are strictly separated into individual modules.
- **Non-technical first** — Every output (titles, descriptions, remediation steps) is written for a marketing executive, not an engineer.
