# Email Authentication Troubleshooter — Backend Refocus & Rearchitecture

## Background

The current backend evolved into a **DNS Configuration Analyzer** with scoring, weights, insight IDs, and business translators. The actual core problem — parsing raw email headers, detecting authentication failures, and generating concrete remediation — was implemented as a secondary, thin layer (`header_analysis/header_parser.py`).

This plan fully rearchitects the backend to treat **raw email headers as the primary input**, promoting the header pipeline to first-class status and demoting or deleting the DNS/scoring machinery.

---

## Task 1 — Full Backend Audit

### File Classification

| File | Classification | Reason | Recommended Action |
|------|---------------|---------|-------------------|
| `main.py` | **KEEP** | FastAPI entry point; structure is correct | Keep as-is |
| `core/orchestrator.py` | **REMOVE** | Primarily glues DNS→RuleEngine pipeline (domain-centric). The `orchestrate_combined_diagnostic` method has the right idea but wraps it in too much complexity. | Delete entirely; replace with a thin `HeaderAnalysisPipeline` |
| `domains/analysis/api.py` | **REFACTOR** | Has the right endpoints (`/headers`, `/combined`) but also exposes the old domain-only route that returns `DomainDiagnosticResponse`. The header endpoint calls the thin `HeaderParser` directly without going through DNS validation. | Refactor: make `/headers` the primary endpoint; demote `/` (domain-only) to a config-check helper |
| `domains/analysis/schemas.py` | **REFACTOR** | Contains `DnsAnalysisResponse`, `SpfResult`, `DkimResult`, `DmarcResult`, `DomainDiagnosticResponse`, `UnifiedDiagnosticResponse`. DNS-centric schemas pollute this file. | Split: keep DNS validation schemas in `dns/schemas.py`; move unified response to `header_analysis/schemas.py` |
| `domains/analysis/aggregator/aggregator.py` | **REFACTOR** | Useful DNS orchestration logic; but tightly coupled to the RuleEngine pipeline. Domain analysis is still needed for remediation (e.g., verifying what SPF record currently exists). | Rename to `DnsVerifier`; make it a supporting tool called by the remediation engine, not the primary pipeline |
| `domains/analysis/aggregator/schemas.py` | **REFACTOR** | `AggregatedAnalysisResponse` is a valid internal type for DNS validation | Rename to `DnsVerificationResult`; keep as internal type |
| `domains/analysis/dns/resolver.py` | **KEEP** | Solid DNS resolver with caching, retries, timeout. Fully reusable. | Keep unchanged; it's infrastructure |
| `domains/analysis/validators/spf.py` | **KEEP** | Good SPF parsing logic. Needed for remediation verification. | Keep; move to `dns/spf_verifier.py` |
| `domains/analysis/validators/dkim.py` | **KEEP** | Good DKIM record parser. Needed for selector verification during remediation. | Keep; move to `dns/dkim_verifier.py` |
| `domains/analysis/validators/dmarc.py` | **KEEP** | Good DMARC record parser. Needed for remediation verification. | Keep; move to `dns/dmarc_verifier.py` |
| `domains/analysis/services/dkim_discovery.py` | **KEEP** | Provider detection is genuinely useful for generating provider-specific remediation steps. | Keep; used by the remediation engine |
| `domains/analysis/exceptions.py` | **KEEP** | DNS error base class. | Keep |
| `domains/analysis/shared/models.py` | **KEEP** | `AnalysisIssue` is the canonical issue type used across validators | Keep; rename to `shared/issue.py` |
| `domains/analysis/scoring/confidence.py` | **REMOVE** | Empty stub. No value. | Delete |
| `domains/analysis/parser/header_parser.py` | **REMOVE** | Empty stub. The real header parser is in `domains/header_analysis/`. | Delete (empty stub) |
| `domains/analysis/recommendations/generator.py` | **REMOVE** | Empty stub. | Delete |
| `domains/analysis/response/builder.py` | **REMOVE** | Empty stub. | Delete |
| `domains/analysis/service.py` | **REMOVE** | Empty stub. | Delete |
| `domains/header_analysis/header_parser.py` | **REFACTOR** | This is the most valuable file in the codebase. Has real parsing logic. But has significant bugs (see Task 4). | Refactor aggressively — split into `parser.py`, `validator.py`, `alignment.py`, `root_cause.py`, `remediation.py` |
| `domains/header_analysis/schemas.py` | **REFACTOR** | `HeaderAnalysisResponse` is the right shape. Needs enrichment: provider info, raw evidence, multi-step remediation. | Extend significantly |
| `domains/rules/engine.py` | **REMOVE** | Detects "insights" from DNS analysis. Does not process headers. Does not detect real authentication failures. Entirely DNS-centric. | Delete entirely |
| `domains/rules/score_calculator.py` | **REMOVE** | Produces misleading deliverability scores from DNS configuration alone. A domain with all DNS records configured but failing authentication would score 100. | Delete entirely |
| `domains/rules/recommendation_mapper.py` | **REFACTOR** | Contains valuable provider-specific step-by-step guidance (Google Workspace, M365, SendGrid, etc.). This content is worth preserving. | Extract provider-specific guidance into `remediation/provider_guides.py`; delete the rest |
| `domains/rules/business_translator.py` | **REMOVE** | Translates insight IDs to marketing-language messages. Not relevant to the troubleshooter use case. | Delete entirely |
| `domains/rules/schemas.py` | **REMOVE** | `RuleEngineResponse`, `DeliverabilityScore`, `ActiveInsight` — all DNS scoring artifacts. | Delete entirely |
| `domains/rules/knowledge/insights.py` | **REMOVE** | 88 lines of insight ID → weight mappings. The entire concept of weighted insight scores is being retired. | Delete entirely |
| `domains/rules/knowledge/recommendations.py` | **KEEP (content)** | The step-by-step fix instructions and sample records are genuinely valuable. | Migrate content to `header_analysis/remediation/provider_guides.py` |
| `domains/rules/knowledge/business_insights.py` | **REMOVE** | Business-language translations. Not needed. | Delete entirely |
| `domains/shared/constants.py` | **KEEP** | Canonical error codes like `MISSING_SPF`, `DNS_ERROR` used by validators. | Keep; possibly extend |
| `shared/models.py` | **KEEP** | `BaseApiResponse`, `FullAnalysisRequest` are still useful | Keep; extend with `HeaderAnalysisRequest` |
| `domains/assistant/` | **REMOVE** | Empty directory. | Delete |
| `domains/automation/` | **REMOVE** | Empty directory. | Delete |
| `domains/reporting/` | **REMOVE** | Empty directory. | Delete |

---

## Task 2 — Dead Architecture Analysis

### Rule Engine
**Verdict: REMOVE**

The `RuleEngine.evaluate()` method takes `AggregatedAnalysisResponse` (DNS results) and detects "insights" like `SPF-001`, `DKIM-001`. It never sees a real email. It cannot determine if a message actually passed or failed authentication. A domain could have a perfectly valid SPF record but still fail SPF on every email (e.g., if sent via a third-party relay). The rule engine would score this domain 100 while every email fails.

### Score Calculator
**Verdict: REMOVE**

The `ScoreCalculator` produces a `DeliverabilityScore` with `band="EXCELLENT"` when a domain has all DNS records present. This is definitionally misleading — DNS configuration is necessary but not sufficient for authentication. A message can be sent from a domain with perfect DNS and still fail DMARC due to alignment issues. The score creates false confidence.

### Business Translator
**Verdict: REMOVE**

Translates technical insight IDs into marketing language. Interesting idea for a consumer product, but adds no troubleshooting value. The user who pasted headers doesn't need "Anyone Can Impersonate Your Brand in Email" — they need to know exactly which DNS record to fix.

### Recommendation Mapper
**Verdict: REFACTOR (content only)**

The `RecommendationMapper` produces good, human-readable fix instructions and sample DNS records. The *content* (step-by-step guides for Google Workspace, M365, SendGrid, Mailchimp, Mailgun, Zendesk) is the most valuable knowledge asset in the codebase. However, the mapper is driven by insight IDs (`DKIM-001`, `SPF-001`) from the DNS pipeline, not from header failures. The mechanism needs to change — but the knowledge content must be preserved.

### Insight Registry
**Verdict: REMOVE**

88 insight ID → severity/weight mappings. The entire insight scoring system is being retired. The content has no value without the scoring system.

### Insight Engine (INSIGHT_REGISTRY detection logic in engine.py)
**Verdict: REMOVE**

See Rule Engine above.

### Scoring Service (ScoreCalculator)
**Verdict: REMOVE**

See Score Calculator above.

### Analysis Engine (AnalysisAggregator)
**Verdict: REFACTOR**

The `AnalysisAggregator` runs DNS lookups + SPF/DKIM/DMARC validators. This is still useful for **remediation verification** (checking whether a recommended fix was applied). But it should no longer be the primary pipeline entry point. Rename to `DnsVerifier` and call it from the remediation engine when the user wants to verify their fix.

---

## Task 3 — Ideal Backend Structure

```
app/backend/
├── main.py                          # FastAPI app + router registration
├── requirements.txt
│
├── shared/
│   ├── models.py                    # BaseApiResponse, request types
│   └── constants.py                 # Canonical error codes (moved from domains/shared/)
│
├── domains/
│   │
│   ├── header_analysis/             # PRIMARY DOMAIN — Header-first pipeline
│   │   ├── __init__.py
│   │   ├── api.py                   # POST /headers (primary), POST /combined
│   │   ├── pipeline.py              # HeaderAnalysisPipeline (replaces orchestrator)
│   │   ├── parser.py                # Raw header parsing, domain extraction
│   │   ├── validator.py             # SPF/DKIM/DMARC result extraction + normalization
│   │   ├── alignment.py             # SPF/DKIM alignment logic
│   │   ├── root_cause.py            # Root cause detection engine
│   │   ├── remediation.py           # Remediation step generator
│   │   └── schemas.py               # All header analysis response types
│   │
│   ├── remediation/                 # Remediation knowledge base
│   │   ├── __init__.py
│   │   ├── provider_guides.py       # Provider-specific step-by-step guides
│   │   └── sample_records.py        # Sample DNS record templates
│   │
│   └── dns/                         # SUPPORTING DOMAIN — DNS verification
│       ├── __init__.py
│       ├── resolver.py              # DNS resolver (moved from analysis/dns/)
│       ├── spf_verifier.py          # SPF record verification (from validators/spf.py)
│       ├── dkim_verifier.py         # DKIM record verification (from validators/dkim.py)
│       ├── dmarc_verifier.py        # DMARC record verification (from validators/dmarc.py)
│       ├── provider_detector.py     # Provider fingerprinting (from services/dkim_discovery.py)
│       └── schemas.py               # DNS-specific types (DnsVerificationResult, etc.)
```

**What disappears entirely:**
- `domains/rules/` — the entire directory is deleted
- `domains/analysis/` — the directory is refactored into `domains/dns/` and content merged into `domains/header_analysis/`
- `core/orchestrator.py` — replaced by `header_analysis/pipeline.py`
- All empty stub files

---

## Task 4 — Current Bugs

### BUG-001: DKIM Key Length Calculation Is Wrong
**File:** `validators/dkim.py` L80-83
**Severity:** HIGH

The code estimates key length as `len(decoded_bytes) * 8`. For RSA, this is incorrect. The DER-encoded ASN.1 key includes header bytes, OID, sequence wrappers. A 2048-bit RSA key decodes to ~294 bytes (2352 bits), not 2048 bits. This causes false classification — a 2048-bit key would be flagged as approaching the `< 1024 bit` threshold incorrectly.

**Fix:** Use `cryptography` library's `load_der_public_key()` to extract actual key size, or compare DER byte length against known thresholds (< 128 bytes = likely < 1024 bits, ≥ 256 bytes = likely ≥ 2048 bits).

---

### BUG-002: SPF Lookup Count Is Static, Not Recursive
**File:** `validators/spf.py` L47-71
**Severity:** HIGH

The SPF lookup count counts `include:`, `a`, `mx`, `ptr`, `exists:` at the top level only. RFC 7208 requires counting **nested** lookups recursively. A record like `v=spf1 include:_spf.google.com ~all` reports 1 lookup but Google's SPF record itself contains 4+ additional lookups. This means the validator produces false negatives — records that actually exceed 10 lookups are reported as within limit.

**Fix:** Implement recursive SPF expansion by resolving each `include:` and counting its mechanisms too. Add a visited-set to prevent infinite recursion.

---

### BUG-003: Authentication-Results Parsing Has False Negatives on Multi-Server Headers
**File:** `header_analysis/header_parser.py` L53-54, L58-60
**Severity:** HIGH

The code joins all `Authentication-Results` headers with ` ; ` and then runs a single regex `\bspf\s*=\s*([a-z]+)`. In real-world emails, multiple `Authentication-Results` headers exist (one per hop). The first match wins. But the first header may be from an untrusted intermediate server that injected a `spf=pass` result. Gmail and other receivers prepend their own result at the top. The code currently takes whichever match comes first, which could be the wrong server's verdict.

**Fix:** Parse each `Authentication-Results` header separately. Use the first one from a trusted server (identified by the `authserv-id` field) or the first/last depending on the provider's convention. At minimum, surface all results, not just the first match.

---

### BUG-004: Alignment Logic Doesn't Account for DMARC adkim/aspf Modes
**File:** `header_analysis/header_parser.py` L39-45
**Severity:** HIGH

The `_aligned()` function implements relaxed alignment as "exact match or either is a subdomain of the other." This is correct for **relaxed** DMARC alignment. However, it does not read the DMARC policy's `adkim=` or `aspf=` tag. If the DMARC policy specifies `adkim=s` (strict), only exact domain matches count — subdomains do not pass. The alignment logic is therefore wrong for strict-mode DMARC policies, producing false positives (reporting alignment PASS when strict mode requires exact match).

**Fix:** The `_aligned()` function must accept an `alignment_mode` parameter (`"r"` or `"s"`). In strict mode, return `True` only when `from_domain == auth_domain`. The DMARC policy's `adkim`/`aspf` values must be extracted from the `Authentication-Results` header or from a DNS lookup.

---

### BUG-005: DMARC Detection in Headers Misses `smtp.mailfrom` Format Variations
**File:** `header_analysis/header_parser.py` L62
**Severity:** MEDIUM

The regex `\b(?:smtp\.mailfrom|envelope-from)\s*=\s*([^\s;]+)` will fail on headers like:
- `smtp.mailfrom=user@example.com` (no space around `=`) — ✅ works
- `smtp.mailfrom="user@example.com"` (quoted) — ❌ fails, picks up the quote as part of the domain
- `envelope-from=<user@example.com>` (angle brackets) — ❌ `_email_domain()` handles this but the regex captures the whole `<user@example.com>` including brackets

**Fix:** Strip quotes and angle brackets from the captured group before passing to `_email_domain()`.

---

### BUG-006: Root Cause Detection Priority Is Wrong
**File:** `header_analysis/header_parser.py` L86-95
**Severity:** HIGH

The `_diagnose()` method checks:
1. DKIM alignment failure
2. SPF alignment failure
3. DKIM authentication failure
4. DMARC failure

**Problem:** It skips the most important case — **SPF authentication failure** (not alignment, but the actual `spf=fail`). If `spf=fail` and `dkim=fail`, neither step 1 nor 2 triggers (they require PASS), but step 3 only catches DKIM. The SPF failure is never detected as a root cause.

Also, the order is wrong for DMARC. DMARC fails because of missing authentication OR missing alignment. The current logic detects DMARC failure AFTER checking individual protocol alignment, but only if `dmarc=FAIL` is explicitly stated. Many providers don't include `dmarc=` in their `Authentication-Results` header at all.

**Fix:** Rewrite `_diagnose()` to check all combinations:
1. SPF FAIL (auth failure) → check first
2. DKIM FAIL (auth failure) → check second  
3. SPF PASS but alignment FAIL
4. DKIM PASS but alignment FAIL
5. Both PASS but neither aligned → DMARC alignment failure
6. DMARC explicitly FAIL
7. Missing authentication entirely (UNKNOWN for both SPF and DKIM)

---

### BUG-007: DKIM-Signature Domain Extraction Uses Wrong Regex
**File:** `header_analysis/header_parser.py` L64
**Severity:** MEDIUM

The regex `r"\bd\s*=\s*([^;\s]+)"` on the `DKIM-Signature` header will match any tag named `d`. But DKIM-Signature tags are separated by semicolons and can have whitespace/newlines (headers can be folded). The regex could match the `d` inside `bh=<hash>` or `b=<signature>` if the hash happens to start with a pattern that looks like `d=`.

**Fix:** Parse the DKIM-Signature header properly using the same tag-value parser already in `DKIMValidator._parse_record()`.

---

### BUG-008: DMARC Validator Doesn't Detect Missing `p=` as a Separate Critical Issue
**File:** `validators/dmarc.py` L58-62
**Severity:** MEDIUM

When `p=` is missing, the code adds a `MISSING_POLICY` issue but then continues processing with `policy=""`. All subsequent checks compare against `["none", "quarantine", "reject"]`, adding an additional `INVALID_POLICY` issue. The response correctly shows `policy=""` but the duplicate issues are misleading.

**Fix:** When `p=` is missing, return early with a single clear issue. Don't add `INVALID_POLICY` when the real problem is `MISSING_POLICY`.

---

### BUG-009: DMARC Version Check Has Double-Reporting
**File:** `validators/dmarc.py` L52-55
**Severity:** LOW

When `v` tag is present but not `DMARC1`, both `INVALID_VERSION` and potentially `MISSING_VERSION` are added (if `v` not in tags). The logic `if tags.get("v") != "DMARC1"` is true when `v` is present-but-wrong AND when `v` is absent. Then `if "v" not in tags` adds a second issue. This results in two issues for one problem.

**Fix:** Use `elif "v" not in tags` for the second check.

---

### BUG-010: `_tag_domain()` Regex Rejects Valid Internationalized Domains
**File:** `header_analysis/header_parser.py` L32
**Severity:** LOW

The regex `r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?"` rejects any domain with uppercase letters (after `.lower()` this is fine) and any punycode domain like `xn--nxasmq6b.com` is technically accepted since it matches the pattern. But domains with underscores (e.g., `_dkim.example.com` — which is a valid DKIM verification domain) would be rejected because `_` is not in the character class.

**Fix:** This only affects `_tag_domain()` which is used for DKIM signing domains extracted from the header. Underscores in the domain itself are not RFC-valid, so this is acceptable for email `From:` domains. Document the limitation.

---

## Task 5 — Migration Roadmap

### P0 — Required Before Hackathon Demo

These must be completed before any demo. The backend must correctly analyze real email headers.

| Priority | Task | Files Affected |
|----------|------|----------------|
| P0.1 | Create `domains/header_analysis/parser.py` — robust header parsing with multi-value `Authentication-Results` handling | New file |
| P0.2 | Create `domains/header_analysis/validator.py` — normalize SPF/DKIM/DMARC results with evidence | New file |
| P0.3 | Create `domains/header_analysis/alignment.py` — alignment logic that accepts adkim/aspf modes | New file |
| P0.4 | Create `domains/header_analysis/root_cause.py` — correct root cause detection covering all 7 failure scenarios | New file |
| P0.5 | Create `domains/header_analysis/remediation.py` — multi-step remediation with provider-specific guidance | New file |
| P0.6 | Extend `domains/header_analysis/schemas.py` — richer response including evidence, confidence, raw results | Modify existing |
| P0.7 | Create `domains/header_analysis/pipeline.py` — single entry point replacing orchestrator | New file |
| P0.8 | Update `domains/analysis/api.py` — make `/headers` primary, clean up obsolete routes | Modify existing |
| P0.9 | Fix BUG-003 (multi-hop Authentication-Results) | `parser.py` |
| P0.10 | Fix BUG-006 (root cause priority and completeness) | `root_cause.py` |
| P0.11 | Fix BUG-004 (strict vs relaxed alignment) | `alignment.py` |
| P0.12 | Delete all empty stubs and dead directories | Multiple files |

### P1 — Important (After P0)

| Priority | Task | Files Affected |
|----------|------|----------------|
| P1.1 | Reorganize `domains/dns/` — move resolver + validators | Move/rename files |
| P1.2 | Create `domains/remediation/provider_guides.py` — migrate step-by-step guides from recommendation_mapper | New file |
| P1.3 | Delete `domains/rules/` entirely (RuleEngine, ScoreCalculator, BusinessTranslator, schemas, knowledge/) | Delete directory |
| P1.4 | Delete `core/orchestrator.py` — replaced by pipeline.py | Delete file |
| P1.5 | Fix BUG-002 (recursive SPF lookup counting) | `dns/spf_verifier.py` |
| P1.6 | Fix BUG-001 (DKIM key length) | `dns/dkim_verifier.py` |
| P1.7 | Fix BUG-005 (quoted/bracketed mailfrom) | `parser.py` |
| P1.8 | Fix BUG-008, BUG-009 (DMARC duplicate issues) | `dns/dmarc_verifier.py` |
| P1.9 | Add `POST /api/v1/headers/verify` endpoint to check if remediation was applied | `api.py` |
| P1.10 | Write tests for all 7 root cause scenarios with real header samples | `tests/` |

### P2 — Future Enhancements

| Priority | Task |
|----------|------|
| P2.1 | Add `POST /api/v1/headers/batch` — analyze multiple headers at once |
| P2.2 | Add confidence scoring to authentication verdicts (e.g., "we found this in header X from server Y") |
| P2.3 | BIMI readiness check (requires `p=reject` + DKIM with 2048-bit key) |
| P2.4 | ARC (Authenticated Received Chain) header parsing for forwarded email analysis |
| P2.5 | Add `POST /api/v1/domain/check` — standalone config-readiness checker (clearly labeled as config only) |
| P2.6 | Async DNS resolution for parallel SPF/DKIM/DMARC lookups |
| P2.7 | PSL-aware organizational domain matching for accurate alignment detection |

---

## Open Questions

> [!IMPORTANT]
> **Q1: Should the `/api/v1/analysis` (domain-only) endpoint be preserved?**
> The current endpoint accepts a domain and returns DNS configuration status. This is still useful as a secondary check but is currently the primary API route. Should it be kept as a supporting endpoint, or removed entirely?

> [!IMPORTANT]
> **Q2: Should scoring be completely removed or rebranded?**
> The `DeliverabilityScore` could be repurposed as a "Configuration Readiness Score" (i.e., how many DNS records are correctly configured). However, it must never claim to represent whether messages are actually delivered. Preference: remove it entirely for the hackathon and add it back later if needed.

> [!IMPORTANT]
> **Q3: Multi-hop Authentication-Results — which server's result should we trust?**
> Real-world emails often have 2-4 `Authentication-Results` headers from different hops. Gmail prepends its own result at the top. Outlook appends at the bottom. We need to decide: always trust the first result? The last? Or expose all of them? Recommendation: parse all, expose all, and highlight the most recent trusted result (first header = most recently added = receiving server's verdict).

> [!WARNING]
> **Breaking change:** Removing `RuleEngineResponse` from the API means any existing frontend calling `POST /api/v1/analysis` will receive a different response shape. The frontend team must be notified before P1.3 executes.
