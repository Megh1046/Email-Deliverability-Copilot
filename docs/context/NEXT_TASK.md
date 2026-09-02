# Next Task

**Document ID:** CTX-004  
**Version:** 4.0  
**Status:** 🟢 ACTIVE  
**Last Updated:** August 2026

---

## Implementation Priorities

The following tasks are ordered by business impact and technical dependency. P0 is the current/active task. P1 through P7 are queued.

---

## P0 — Documentation Synchronization ✅ (Active)

**Objective:** Update all context documentation to accurately reflect the current implementation.

**Current state:** Context files described the previous architecture (`IntelligenceOrchestrator`, `RuleEngine`, `AnalysisAggregator`, DNS-only analysis). These modules have been replaced by the `HeaderAnalysisPipeline`.

**Implementation area:** `docs/context/`

**Acceptance criteria:**
- [x] `PROJECT_CONTEXT.md` describes current architecture accurately
- [x] `CURRENT_STATE.md` describes what actually works right now
- [x] `DECISIONS.md` documents actual architectural decisions
- [x] `NEXT_TASK.md` reflects actual next priorities
- [x] `CHANGELOG.md` records architectural evolution
- [ ] README.md updated with basic setup instructions
- [ ] API documentation updated with correct endpoint and schema

---

## P1 — User-Friendly Raw-Header Input (Frontend)

**Objective:** Create a minimal frontend that allows a user to paste raw email headers into a text area and receive a formatted analysis result — without needing to understand JSON.

**Current state:** No frontend exists. Users must construct a JSON request manually. Pasting raw headers directly into the HTTP body returns `HTTP 422 Unprocessable Entity`.

**The JSON wrapping problem:**

The API expects:
```json
{ "headers": "<raw email headers as a string>" }
```

If a user pastes headers directly (without JSON wrapping), the server returns:
```
422 Unprocessable Entity — json_invalid — Expecting property name enclosed in double quotes
```

This is not an email-parsing failure. It is a request formatting error that a frontend must silently handle.

**Implementation area:** `app/frontend/` — new frontend application

**Acceptance criteria:**
- [ ] A text area where users paste raw email headers
- [ ] "Analyze" button triggers `POST /api/v1/analysis/headers` with headers wrapped in JSON
- [ ] Results displayed in plain English (SPF, DKIM, DMARC pass/fail, alignment, root cause, remediation steps)
- [ ] Users never see JSON or HTTP terminology
- [ ] Error states handled gracefully (empty input, server error)

**Dependencies:** None — the API endpoint is already operational.

---

## P2 — Automatic Provider Detection from Header Evidence

**Objective:** Detect the sending email provider from header evidence without requiring a `provider_hint` from the user.

**Current state:** Provider detection in the `HeaderAnalysisPipeline` requires an explicit `provider_hint`. Without it, `provider = null` and remediation is generic. The user should not need to know which provider their company uses.

**Implementation area:** `app/backend/domains/header_analysis/pipeline.py` (new provider detection stage)

**How it should work:**
1. Inspect SPF domain (e.g., `amazonses.com` → Amazon SES, `sendgrid.net` → SendGrid)
2. Inspect DKIM signing domain (e.g., `sendgrid.net`, `mailchimp.com`)
3. Inspect `Received:` headers for known infrastructure hostnames
4. Match against `PROVIDER_CATALOG` fingerprints
5. Assign confidence: HIGH (multiple matches), MEDIUM (one match), LOW (weak match)

**Acceptance criteria:**
- [ ] `HeaderAnalysisPipeline` auto-detects provider from header evidence
- [ ] Confidence levels are signal-derived (not hardcoded to MEDIUM)
- [ ] Known providers detected: Google Workspace, Microsoft 365, Amazon SES, SendGrid, Mailchimp, Mailgun, Zendesk
- [ ] Falls back to `provider_hint` if detection is inconclusive
- [ ] `provider` field populated correctly in `HeaderAnalysisResponse`

**Dependencies:** P1 (frontend) is independent; this can run in parallel.

---

## P3 — Provider-Specific Actionable Remediation

**Objective:** Enhance remediation steps to be fully click-by-click guides for each detected provider, rather than generic protocol-level instructions.

**Current state:** `PROVIDER_DKIM_GUIDES` and `PROVIDER_SPF_INCLUDES` in `domains/remediation/provider_guides.py` provide provider-specific content, but only when the provider is known. The guides contain step-by-step admin UI instructions.

**Current gap:** The guides may not reflect the most current UI paths for each provider. They are static strings that need periodic review and updating.

**Example of the target output for a DKIM alignment failure with SendGrid as provider:**

```
Problem: DKIM is authenticated but not aligned with the From domain.
Provider: SendGrid

Step 1: Log in to SendGrid at app.sendgrid.com.
Step 2: Go to Settings → Sender Authentication.
Step 3: Click "Authenticate Your Domain".
Step 4: Enter your From domain (e.g., example.com).
Step 5: SendGrid will show two CNAME records (s1._domainkey and s2._domainkey).
Step 6: Copy both CNAME records.
Step 7: In your DNS provider, create both CNAME records exactly as shown.
Step 8: Return to SendGrid and click "Verify".
Step 9: Send a test email and paste the new headers into Email Deliverability Copilot.
Step 10: Confirm that dkim=pass and the DKIM domain matches your From domain.
```

**Implementation area:** `app/backend/domains/remediation/provider_guides.py`

**Acceptance criteria:**
- [ ] All 7 supported providers have verified, up-to-date DKIM guides
- [ ] SPF include directives are correct for all 7 providers
- [ ] Provider detection (P2) populates provider context for all guides
- [ ] Each guide ends with a verification step ("re-analyze headers")

**Dependencies:** P2 (automatic provider detection) should be completed first so the guides are actually triggered.

---

## P4 — Frontend Result Presentation

**Objective:** Display analysis results in a clear, visually structured format for non-technical users.

**Current state:** Frontend is not started.

**What the results page should show:**
- Pass/Fail status cards for SPF, DKIM, DMARC
- Alignment status (SPF aligned, DKIM aligned, overall)
- Detected provider (if known)
- Root cause — headline and plain-English explanation
- Remediation steps — numbered list with copyable DNS records and verification commands
- Raw evidence section (collapsible) for technical users

**Implementation area:** `app/frontend/`

**Dependencies:** P1 (basic frontend scaffolding).

---

## P5 — Testing: Fix Stale Tests, Add Pipeline Coverage

**Objective:** Ensure the test suite accurately tests the current codebase.

**Current state:** Multiple test files in `app/backend/tests/` reference modules from the previous architecture that no longer exist. These tests are likely failing.

**Files to fix or remove:**

| File | Action Needed |
|------|--------------|
| `test_pipeline.py` | Rewrite — references `domains.analysis.api` and old schemas |
| `test_aggregator.py` | Remove or rewrite — `AnalysisAggregator` removed |
| `test_orchestrator.py` | Remove or rewrite — `IntelligenceOrchestrator` removed |
| `test_rule_engine.py` | Remove or rewrite — `RuleEngine` removed |
| `test_rule_engine_consistency.py` | Remove or rewrite — `RuleEngine` removed |
| `test_header_analysis.py` | Update — migrate from deprecated `HeaderParser` shim to `HeaderAnalysisPipeline` directly |

**New tests needed:**
- [ ] `test_parser.py` — unit tests for `HeaderParser` / `parser.py`
- [ ] `test_validator.py` — unit tests for `AuthenticationValidator`
- [ ] `test_alignment.py` — unit tests for `check_alignment()` covering all edge cases
- [ ] `test_root_cause.py` — unit tests for all 8 root cause codes
- [ ] `test_remediation.py` — unit tests for each remediation generator
- [ ] `test_api_headers.py` — integration tests for `POST /api/v1/analysis/headers`
- [ ] Verified test scenarios (see [Verified Test Scenarios](CURRENT_STATE.md))

**Implementation area:** `app/backend/tests/`

---

## P6 — Better Provider Detection Coverage

**Objective:** Improve provider detection accuracy and coverage.

**Current limitations:**
- Amazon SES uses random 32-character DKIM selectors — cannot be detected by selector fingerprint
- The `DICTIONARY_CATALOG` fallback selectors were removed from the `DKIMDiscoveryService` discover path (only the first element of the selector list is used, and common dictionary selectors are not probed)
- Some providers (e.g., Constant Contact, HubSpot, Brevo/Sendinblue) are not in the catalog

**Improvement areas:**
- Add more providers to `PROVIDER_CATALOG` in `domains/dns/provider_detector.py`
- Add `Received:` header inspection for infrastructure hostname matching
- Consider SPF domain substring matching in the pipeline (not just via DNS lookup)

---

## P7 — Production Hardening

**Objective:** Make the API production-ready.

**Items:**
- [ ] CI/CD pipeline — configure GitHub Actions to run tests on PR
- [ ] Input validation hardening — rate limiting, request size limits
- [ ] Error handling — structured error responses for all failure modes
- [ ] Logging — request/response logging with sanitization
- [ ] Environment configuration — `config/` directory currently exists but content is unclear
- [ ] Containerization — Dockerfile for backend
- [ ] Health check endpoint — extend `GET /` or add `GET /health`
- [ ] README update — setup instructions, local dev guide

---

## Deferred (Not Currently Prioritized)

These were planned in earlier documentation but are not currently scheduled:

| Item | Reason Deferred |
|------|----------------|
| AI Assistant / LLM integration | Core analysis must be solid first; AI adds cost/complexity |
| PostgreSQL database | No persistence needed for MVP; stateless API is simpler |
| Reporting domain (PDF/JSON export) | Not yet needed |
| Cloudflare DNS automation | Advanced feature; basic remediation guidance comes first |
| Multi-user accounts / authentication | V2 feature |
