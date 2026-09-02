# Changelog

**Document ID:** CTX-005  
**Version:** 2.0  
**Status:** 🟢 ACTIVE  
**Last Updated:** August 2026

---

## Format

All notable changes to this project are documented in this file.

Entries before v0.5.0 used date-based versioning. Starting from v0.5.0, entries reflect the actual implementation state verified against the codebase.

---

## [0.5.0] — August 2026 — Architecture Pivot: Header Analysis Pipeline

### Summary

The system architecture was redesigned from a DNS-only domain scoring platform to a real email header analysis pipeline. The previous `IntelligenceOrchestrator` / `RuleEngine` / `AnalysisAggregator` architecture was replaced by the `HeaderAnalysisPipeline`.

### Added

- `app/backend/domains/header_analysis/` — New primary analysis domain containing the complete 5-stage pipeline:
  - `pipeline.py` — `HeaderAnalysisPipeline` — 5-stage orchestrator (Parse → Validate → Align → Root Cause → Remediate)
  - `parser.py` — `HeaderParser` — Parses raw email headers per RFC 5322 and RFC 8601; extracts From domain, Return-Path domain, DKIM-Signature domain, all `Authentication-Results` headers
  - `validator.py` — `AuthenticationValidator` — Normalizes raw result strings to `PASS | FAIL | UNKNOWN`
  - `alignment.py` — `check_alignment()` — RFC 7489 SPF and DKIM alignment with relaxed and strict mode support
  - `root_cause.py` — `detect_root_cause()` — 8-case priority decision tree for root cause identification
  - `remediation.py` — `generate_remediation()` — Provider-aware ordered remediation steps
  - `schemas.py` — `HeaderAnalysisResponse`, `AuthEvidence`, `AuthenticationResult`, `AlignmentResult`, `RootCause`, `RemediationStep`, `ProviderInfo`
  - `api.py` — `POST /api/v1/analysis/headers` (primary endpoint) and `POST /api/v1/analysis/headers/verify` (DNS verification endpoint)
  - `header_parser.py` — Deprecated backward-compatibility shim (delegates to `HeaderAnalysisPipeline`)

- `app/backend/domains/remediation/provider_guides.py` — `PROVIDER_DKIM_GUIDES` and `PROVIDER_SPF_INCLUDES` for 7 providers: Google Workspace, Microsoft 365, SendGrid, Mailchimp, Mailgun, Amazon SES, Zendesk

- `app/backend/domains/header_analysis/schemas.py` — Complete response contract for `POST /api/v1/analysis/headers`:
  - `HeaderAnalysisResponse` — Top-level response
  - `AuthEvidence` — Per-header evidence extracted from `Authentication-Results`
  - `AuthenticationResult` — Normalized per-protocol result
  - `AlignmentResult` — SPF, DKIM, and overall alignment status
  - `RootCause` — Primary failure classification
  - `RemediationStep` — Single ordered fix step
  - `ProviderInfo` — Detected provider with confidence level

### Bug Fixes Applied During Implementation

- **BUG-003** — Multi-hop Authentication-Results handling: All headers are now parsed individually; the first header (prepended by the final MTA) is used as the primary trusted verdict.
- **BUG-004** — Alignment mode was always relaxed: `check_alignment()` now accepts explicit `spf_mode` and `dkim_mode` parameters.
- **BUG-006** — Root cause decision tree: The original `_diagnose()` missed SPF authentication failure entirely and had incorrect priority ordering. The 8-case tree now correctly handles all cases with explicit priorities.
- **BUG-007** — DKIM-Signature `d=` parsing: Now uses proper semicolon-delimited tag-value parsing instead of a bare regex that could match characters inside the `b=` signature blob.
- **BUG-005** — Quoted/bracketed `smtp.mailfrom` values are now stripped before domain extraction.

### Changed

- `app/backend/main.py` — Updated to register the `header_analysis` router at `/api/v1` instead of the old `analysis` router.

### Architecture Note

The old architecture (`IntelligenceOrchestrator`, `RuleEngine`, `AnalysisAggregator`, `ScoreCalculator`, `BusinessTranslator`, `RecommendationMapper`) has been superseded by the `HeaderAnalysisPipeline`. Old module paths (`core/orchestrator.py`, `domains/rules/`, `domains/analysis/`) **no longer exist** in the codebase.

---

## [0.5.1] — August 2026 — Real Email Header Validation

### Summary

The `HeaderAnalysisPipeline` was validated against real-world email headers from a Simplilearn marketing email delivered via Amazon SES.

### Verified

- **Test scenario:** Simplilearn marketing email sent through Amazon SES.
- **From domain:** `simplilearn.training`
- **Return-Path domain:** `mailer.simplilearn.training`
- **DKIM signing domain:** `simplilearn.training`
- **SPF result:** PASS
- **DKIM result:** PASS
- **DMARC result:** PASS
- **SPF alignment:** True (relaxed — `mailer.simplilearn.training` aligns with `simplilearn.training`)
- **DKIM alignment:** True (exact match — `simplilearn.training`)
- **Overall alignment:** True
- **Provider:** Amazon SES (via `provider_hint`)
- **`passed`:** True
- **`root_cause`:** null
- **`remediation`:** []

This confirms that the pipeline correctly processes real-world headers from a production sending service (Amazon SES) and produces accurate results for an email that passes all authentication checks.

---

## [0.5.2] — August 2026 — Documentation Synchronization

### Summary

All context documentation was updated to accurately reflect the current codebase. Previous documentation described the old DNS-only architecture and is now replaced.

### Changed

- `docs/context/PROJECT_CONTEXT.md` — Complete rewrite: current architecture, API endpoints, schemas, alignment logic, provider detection, root cause engine, remediation system, deprecation notice for old architecture
- `docs/context/CURRENT_STATE.md` — Complete rewrite: actual working features, stale test inventory, JSON input limitation, real email test documentation
- `docs/context/DECISIONS.md` — Complete rewrite: new architectural decisions (ARCH-H1 through ARCH-H9); old decisions preserved with current-status annotations
- `docs/context/NEXT_TASK.md` — Complete rewrite: actual P0-P7 priority list replacing obsolete M3A task
- `docs/context/CHANGELOG.md` — Updated with architecture transition history

---

## [0.4.2] — August 2026 — DKIM Selector Discovery Service (M2F.3)

> **⚠️ Historical:** The modules referenced in this entry (`domains/analysis/services/dkim_discovery.py`, `AnalysisAggregator`, `RecommendationMapper`, `RuleEngine`) no longer exist in the current codebase. This entry is preserved for historical record only.

### Added (Historical)
- Created `app/backend/domains/analysis/services/dkim_discovery.py` containing `DKIMDiscoveryService`.
  - `PROVIDER_CATALOG` with 7 ESPs: Google Workspace, Microsoft 365, SendGrid, Mailchimp, Mailgun, Zendesk, Amazon SES.
  - `DICTIONARY_CATALOG` with 8 high-probability fallback selectors.
  - `discover_selectors()` method: priority-ordered candidate list generation, MX/SPF fingerprinting, 11-lookup budget enforcement.
- Added `provider: Optional[str] = None` field to `DkimResult` in `domains/analysis/schemas.py`.
- 30 new discovery and integration tests.

> **Current status of `DKIMDiscoveryService`:** Still exists at `app/backend/domains/dns/provider_detector.py`, used only by the DNS verification endpoint (`POST /api/v1/analysis/headers/verify`). Not used by the primary header analysis pipeline.

---

## [0.4.1] — August 2026 — Rule Engine Consistency Enforcement (M2F.1)

> **⚠️ Historical:** The `RuleEngine`, `ScoreCalculator`, `BusinessTranslator` referenced in this entry no longer exist. Preserved for historical record.

### Changed (Historical)
- `DMARC-017` weight changed from `+10` to `0`.
- `BusinessTranslator` expanded with `HEALTHY_BIZ_INSIGHTS` suppression logic.
- `BIZ-015` contradiction bug fixed.

---

## [0.4.0] — July 2026 — Architecture Hardening (M2F)

> **⚠️ Historical:** `core/orchestrator.py` (`IntelligenceOrchestrator`), `FullAnalysisRequest` as the public API model, and all `domains/rules/` modules referenced here no longer exist. Preserved for historical record.

### Added (Historical)
- Created `core/orchestrator.py` containing `IntelligenceOrchestrator`.
- Created `FullAnalysisRequest` in `shared/models.py`.
- 10 new orchestrator tests.

---

## [0.3.1] — July 2026 — Public API Contract Stabilization (M2E)

> **⚠️ Historical:** `RuleEngineResponse`, `BaseApiResponse` inheriting from it, and the domain-level `POST /api/v1/analysis` endpoint no longer exist. Preserved for historical record.

---

## [0.3.0] — July 2026 — Rule Engine (M2C)

> **⚠️ Historical:** `domains/rules/engine.py` (RuleEngine), `ScoreCalculator`, `RecommendationMapper`, `BusinessTranslator`, `RuleEngineResponse` no longer exist. Preserved for historical record.

---

## [0.2.1] — July 2026 — Knowledge Base Refinement (M2B.1)

> **⚠️ Historical:** Confidence scoring model, severity weights, and `DKB-*` knowledge base files referenced here were part of the old RuleEngine architecture. Preserved for historical record.

---

## [0.2.0] — July 2026 — Deliverability Knowledge Base (M2B)

> **⚠️ Historical:** Knowledge base documents in `docs/knowledge/` and 75 technical insights referenced here were consumed by the old RuleEngine. Preserved for historical record.

---

## [0.1.4] — July 2026 — DMARC Intelligence Engine (M1E)

### Added
- Created `DMARCValidator` — currently lives at `app/backend/domains/dns/dmarc_verifier.py`.
- Shared models `DomainRequest` and `AnalysisIssue` in `shared/models.py`.

> **Current status:** `DMARCValidator` is still active in `domains/dns/dmarc_verifier.py`, used by the verify endpoint.

---

## [0.1.3] — July 2026 — DKIM Intelligence Engine (M1D)

### Added
- Created `DKIMValidator` — currently lives at `app/backend/domains/dns/dkim_verifier.py`.

> **Current status:** `DKIMValidator` is still active in `domains/dns/dkim_verifier.py`, used by the verify endpoint.

---

## [0.1.2] — July 2026 — SPF Intelligence Engine (M1C)

### Added
- Created `SPFValidator` — currently lives at `app/backend/domains/dns/spf_verifier.py`.

> **Current status:** `SPFValidator` is still active in `domains/dns/spf_verifier.py`, used by the verify endpoint.

---

## [0.1.1] — July 2026 — DNS Intelligence Service (M1B)

### Added
- Created `DNSResolver` — currently lives at `app/backend/domains/dns/resolver.py`.
- A, AAAA, MX, TXT, NS, CNAME, SOA record types supported. Retry logic with bounded backoff. Per-request cache.

> **Current status:** `DNSResolver` is still active in `domains/dns/resolver.py`, used by the verify endpoint.

---

## [0.1.0] — July 2026 — Project Scaffold

### Added
- Repository initialized with MIT license, `.gitignore`, `.env.example`
- Documentation architecture locked
- Backend scaffold: FastAPI entry point, domain folder structure
- Frontend scaffold: directory structure (no framework installed)
- AI development layer: placeholders
- Scripts: placeholder files
- Test directory structure: `tests/backend/`, `tests/frontend/`, `tests/integration/`
- Assets directory
- GitHub workflows directory (empty)

---

## [0.0.0] — Project Onboarding

### Added
- Project context files created (`docs/context/`)
- Initial `PROJECT_CONTEXT.md`, `CURRENT_STATE.md`, `DECISIONS.md`, `NEXT_TASK.md`, `CHANGELOG.md`
