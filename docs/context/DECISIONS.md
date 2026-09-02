# Decisions Log

**Document ID:** CTX-003  
**Version:** 2.0  
**Status:** 🟢 ACTIVE  
**Last Updated:** August 2026

---

## Purpose

This document records all architectural and product decisions made for the project. Each decision includes the rationale, alternatives considered where known, and current status.

---

## Product Decisions

| ID | Decision | Reason | Status |
|----|----------|--------|--------|
| DEC-001 | Primary user is the Marketing Executive | Marketing teams face deliverability issues but lack DNS expertise; solving their problem drives the most value | 🟢 Active |
| DEC-002 | Product category is Email Deliverability Copilot | Positions the tool as an intelligent troubleshooter, not just a DNS record checker | 🟢 Active |
| DEC-003 | Primary workflow: Paste headers → Get diagnosis → Get fix | Every user interaction ends with a clear, actionable next step | 🟢 Active |
| DEC-004 | Output language targets non-technical users | Root cause descriptions, remediation steps, and summaries are written for a marketing executive, not an engineer | 🟢 Active |

---

## Architectural Decisions (Current Architecture)

### ARCH-H1 — Header-Based Analysis as Primary Input

**Decision:** The primary analysis mode is parsing raw email headers (including `Authentication-Results` headers), not DNS-only lookup.

**Why:** DNS-only analysis shows what records are configured but cannot reveal what actually happened when a specific email was delivered. Real email headers contain the receiving MTA's verdict (`spf=pass`, `dkim=fail`, etc.) — this is ground truth. A user can paste headers from any failed email and get a definitive diagnosis.

**Alternatives considered:** DNS-only analysis (showing configured records but not delivery outcome). This was the original architecture and was found insufficient.

**Chosen approach:** Parse raw email headers as the primary input. DNS-based verification is a secondary, supplementary step.

**Current status:** Implemented. `HeaderAnalysisPipeline` is the primary pipeline.

**Consequences:** Users must paste headers from received emails (not sent-message headers). If headers lack `Authentication-Results`, the system cannot determine the cause.

---

### ARCH-H2 — Pipeline Architecture (5 Stages)

**Decision:** The header analysis pipeline is organized as five distinct, composable stages: Parse → Validate → Align → Root Cause → Remediate.

**Why:** Separation of concerns. Each stage has a single, clear responsibility. The parser makes no judgments. The validator makes no DNS calls. The alignment checker knows nothing about remediation. This makes each stage independently testable and replaceable.

**Chosen approach:** `HeaderParser` → `AuthenticationValidator` → `check_alignment()` → `detect_root_cause()` → `generate_remediation()`, orchestrated by `HeaderAnalysisPipeline`.

**Current status:** Implemented. All five stages are in `app/backend/domains/header_analysis/`.

---

### ARCH-H3 — Authentication-Results as Primary Evidence

**Decision:** The `Authentication-Results` header (RFC 8601), specifically the first one prepended by the final receiving MTA, is the primary trusted evidence for SPF, DKIM, and DMARC verdicts.

**Why:** The receiving MTA is the authoritative source of authentication verdicts. Multiple `Authentication-Results` headers may be present in a forwarded or multi-hop email; only the first (outermost, prepended by the final MTA) is trusted.

**Consequences:** If `Authentication-Results` is absent, the system returns `NO_HEADERS` root cause with instructions to retrieve complete headers.

**Current status:** Implemented in `parser.py`. Bug fix BUG-003 addressed multi-hop header handling.

---

### ARCH-H4 — Separation of Authentication from Alignment

**Decision:** Authentication (did the protocol pass?) and alignment (does the authenticated domain match From?) are computed separately and reported separately.

**Why:** They are distinct concepts that fail for different reasons and require different fixes. SPF can authenticate a domain that is not aligned with From. DMARC requires both authentication AND alignment. Conflating them obscures the root cause.

**Example:**
- SPF = PASS (the sending IP is authorized for `sendgrid.net`)
- SPF alignment = FALSE (from domain is `example.com`, which is not `sendgrid.net`)
- DMARC = FAIL (no aligned authentication path)

**Current status:** Implemented. `AuthenticationResult` and `AlignmentResult` are separate schemas.

---

### ARCH-H5 — Relaxed and Strict Alignment Modes

**Decision:** The system supports both RFC 7489 relaxed and strict alignment modes, accepting them as explicit parameters.

**Why:** DMARC records can specify `aspf=r` (relaxed) or `aspf=s` (strict) and the same for `adkim=`. The alignment check must honor this. Defaulting to relaxed matches standard practice (most DMARC policies use relaxed).

**Relaxed:** Organizational domain match. `mail.example.com` aligns with `example.com`.

**Strict:** Exact match. `mail.example.com` does NOT align with `example.com`.

**Current status:** Implemented in `alignment.py`. Bug fix BUG-004 addressed the original code always using relaxed regardless of mode.

---

### ARCH-H6 — Root Cause Priority Decision Tree

**Decision:** Root cause detection uses a strict 8-case priority tree. Only the highest-priority failure is reported as the root cause.

**Why:** A single, clear root cause is more actionable than a list of problems. Priority order ensures the most fundamental failure is reported first (e.g., SPF authentication failure is more fundamental than alignment failure).

**Current status:** Implemented in `root_cause.py`. Bug fix BUG-006 corrected priority ordering and added the missing SPF_AUTH_FAIL case.

---

### ARCH-H7 — Provider-Aware Remediation

**Decision:** Remediation steps are injected with provider-specific content when the sending provider is known.

**Why:** Generic instructions ("configure DKIM") are not actionable for most users. Provider-specific steps ("Log in to SendGrid → Settings → Sender Authentication → Domain Authentication") reduce friction and errors.

**Current limitation:** The provider must be supplied via `provider_hint` in the API request. Automatic provider detection from headers is not yet implemented.

**Current status:** Implemented in `remediation.py` and `domains/remediation/provider_guides.py`. Seven providers supported.

---

### ARCH-H8 — Two Distinct API Endpoints

**Decision:** Two endpoints are provided: one for header analysis, one for DNS verification.

- `POST /api/v1/analysis/headers` — analyzes raw email headers (no DNS calls)
- `POST /api/v1/analysis/headers/verify` — performs live DNS verification

**Why:** Header analysis and DNS verification serve different user needs. Header analysis diagnoses what happened to a specific email. DNS verification confirms that a fix has been applied correctly in DNS.

**Current status:** Both endpoints implemented in `domains/header_analysis/api.py`.

---

### ARCH-H9 — `HeaderParser` Shim is Deprecated

**Decision:** The `header_parser.py` file (`HeaderParser` class) is kept only as a backward-compatibility shim. New code must use `HeaderAnalysisPipeline` directly.

**Why:** Early versions of the test suite referenced `HeaderParser` directly. The shim avoids breaking those tests while signaling the correct entry point.

**Current status:** `header_parser.py` exists and issues a `DeprecationWarning`. Test files that use it should be migrated to `HeaderAnalysisPipeline`.

---

## Development Decisions

| ID | Decision | Reason | Status |
|----|----------|--------|--------|
| DEV-001 | Documentation-Driven Development | Documentation written before code; docs are the source of truth | 🟢 Active |
| DEV-002 | AI-assisted development with repo-embedded context files | AI models read context files before making changes; ensures consistency | 🟢 Active |
| DEV-003 | No authentication in MVP | Reduces scope for V1 | 🟡 Proposed |
| DEV-004 | Frontend hides JSON complexity from users | Users paste raw text; frontend constructs the JSON request | 🔴 Not yet implemented |

---

## Scope Decisions

| ID | Decision | Reason | Status |
|----|----------|--------|--------|
| SCOPE-001 | V1 excludes: campaign creation, email sending, CRM, contact management, billing, notifications, mobile app | Keeps MVP focused on the core deliverability workflow | 🟢 Active |
| SCOPE-002 | V1 excludes: multi-user collaboration, enterprise roles | Single-user flow first | 🟢 Active |
| SCOPE-003 | Remediation is generic-first, provider-specific-second | Generic remediation works for all users; provider-specific is an improvement when provider is known | 🟡 Partially implemented |

---

## Previously Recorded Architecture Decisions (Partially Obsolete)

The following decisions were recorded under the previous architecture. The modules they reference no longer exist; however, the underlying principles they captured are partially preserved in the current implementation.

| Old ID | Decision | Current Status |
|--------|----------|---------------|
| ARCH-001 | Domain-oriented backend architecture | 🟢 Still applies — `domains/` structure is preserved |
| ARCH-002 | Frontend: Next.js + React + TypeScript + TailwindCSS | 🔴 Not yet implemented |
| ARCH-003 | Backend: FastAPI + Python | 🟢 Still applies |
| ARCH-004 | Database: PostgreSQL | 🔴 Not implemented |
| ARCH-005 | AI provider: OpenAI-compatible | 🔴 Not implemented |
| ARCH-006 | Containerized deployment | 🔴 Not implemented |
| ARCH-007 | Shared Models Module (`shared/models.py`) | 🟢 Still applies — `shared/models.py` exists with `AnalysisIssue`, `DomainRequest` |
| ARCH-008 | Knowledge Base as source of truth | ❌ Obsolete — `RuleEngine` and static knowledge registry removed |
| ARCH-009 | Knowledge Base Scoring Refinements | ❌ Obsolete — scoring model removed |
| ARCH-010 | Rule Engine as Central Intelligence Layer | ❌ Obsolete — `RuleEngine` removed |
| ARCH-011 | Centralized Runtime Knowledge Registry | ❌ Obsolete — replaced by `root_cause.py` + `remediation.py` |
| ARCH-012 | End-to-End Intelligence Pipeline | ❌ Obsolete — replaced by `HeaderAnalysisPipeline` |
| ARCH-013 | `RuleEngineResponse` as Sole Public Contract | ❌ Obsolete — replaced by `HeaderAnalysisResponse` |
| ARCH-014 | Orchestration Layer Pattern (`IntelligenceOrchestrator`) | ❌ Obsolete — `core/orchestrator.py` does not exist |
| ARCH-015 | Rule Engine Consistency Enforcement | ❌ Obsolete — `RuleEngine` removed |
| ARCH-016 | DKIM Discovery Layer | 🟡 Partially applies — `DKIMDiscoveryService` still exists in `domains/dns/provider_detector.py` but is only used by the verify endpoint, not the primary pipeline |
