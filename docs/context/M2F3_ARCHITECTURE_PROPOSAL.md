# M2F.3 — DKIM Selector Discovery & Validation Architecture Proposal

**Status:** Formal Proposal (Pre-Implementation)  
**Objective:** Replace static, hardcoded DKIM validation with dynamic, multi-stage selector discovery to resolve the 95% false-positive rate for `DKIM-001` observed in M2F.2.

---

## 1. Architecture Document

The current architecture relies on a strict 1:1 input to the `DKIMValidator` (e.g., test domain `example.com` with static selector `google`). M2F.3 introduces a decoupling between the Orchestrator and Validator through a new **Discovery Layer**.

### Workflow
1. **Phase 1: DNS Context Gathering:** The Orchestrator collects the domain's TXT (SPF) and MX records before DKIM validation.
2. **Phase 2: Provider Fingerprinting:** The `DKIMDiscoveryService` compares the SPF and MX records against a known catalog of Email Service Providers (ESPs).
3. **Phase 3: Targeted Probing:** If a provider is identified, the service prioritizes testing that provider's standard DKIM selectors.
4. **Phase 4: Dictionary Fallback:** If no provider is identified, or provider-specific probes fail, a short dictionary of ubiquitous fallback selectors is probed.
5. **Phase 5: Short-Circuit Evaluation:** The system stops probing the moment a valid DKIM record is found (Short-Circuit Evaluation) to conserve DNS lookup budget.

---

## 2. DNS Lookup Budget

Aggressive DNS probing can lead to timeouts, latency, and rate-limiting from upstream resolvers. A strict DNS budget will be enforced.

- **Current Budget:** 1 query (static selector).
- **Proposed M2F.3 Budget per Domain:**
  - **Base Lookups (Pre-requisites):** 2 queries (1 MX, 1 TXT for SPF). *Already performed by other validators.*
  - **Targeted Probes (Provider matched):** 1–3 queries.
  - **Dictionary Fallback Probes:** Max 8 queries.
  - **Total Maximum DKIM Queries:** 11 queries.
- **Optimization Strategy:**
  - **Short-circuiting:** Probing halts immediately upon the first successful `v=DKIM1` record resolution. Most domains on standard infrastructure will complete in **1–2 queries**.
  - **Concurrent Resolution:** Fallback dictionary probes should be dispatched concurrently where possible.

---

## 3. Provider Fingerprint Catalog

A mapping of common ESP footprints (found in MX and SPF) to their default DKIM selectors.

| Provider | MX Footprint | SPF Footprint (`include:`) | Default Selectors |
|----------|--------------|---------------------------|-------------------|
| **Google Workspace** | `aspmx.l.google.com` | `_spf.google.com` | `google` |
| **Microsoft 365** | `mail.protection.outlook.com` | `spf.protection.outlook.com` | `selector1`, `selector2` |
| **SendGrid** | `mx.sendgrid.net` | `sendgrid.net` | `s1`, `s2` |
| **Mailchimp** | - | `servers.mcsv.net`, `spf.mandrillapp.com` | `k1`, `k2`, `k3` |
| **Mailgun** | `mxa.mailgun.org` | `mailgun.org` | `pic`, `krs`, `mg`, `mailo` |
| **Zendesk** | - | `mail.zendesk.com` | `zendesk1`, `zendesk2` |
| **Amazon SES** | `smtp.receptor.amazon.com` | `amazonses.com` | *Custom 32-char (Dictionary fallback)* |

> **Note on Custom Infrastructure (GitHub, OpenAI):** These organizations generally route mail through vendors like SendGrid, Mailgun, or Google Workspace. They will automatically be identified via Phase 2 Fingerprinting (e.g., GitHub's SPF includes SendGrid/Mailgun footprints).

---

## 4. Selector Dictionary Catalog

For custom setups, legacy infrastructures, or unrecognized ESPs, the system will execute a fallback probe using a highly targeted dictionary. 

**Top 8 High-Probability Selectors (Ordered by Priority):**
1. `default`
2. `mail`
3. `api`
4. `smtp`
5. `s1`
6. `k1`
7. `m1`
8. `dkim`

*These 8 selectors, combined with the Provider Catalog, account for an estimated 95%+ of standard corporate deployments.*

---

## 5. Scoring Impact Analysis

- **Current State:** 96% of domains falsely trigger `DKIM-001` (CRITICAL, -20 points) because the provided static selector does not exist.
- **Post-M2F.3 State:**
  - **Positive Impact:** Valid domains will recover 20 points and accurately shift into `GOOD` or `EXCELLENT` bands.
  - **Negative Impact (True Negatives):** Domains genuinely lacking DKIM will still trigger `DKIM-001`.
  - **Contextual Recommendations:** If `DKIM-001` fires, but a provider (e.g., Microsoft 365) was fingerprinted, the recommendation text will become dynamic: *"We detected Microsoft 365 infrastructure. Ensure you have configured `selector1` and `selector2` in your DNS."*

---

## 6. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Increased Latency** | High | Medium | Implement short-circuit evaluation. Probe halts on first success. Strict overall timeout on the `DKIMDiscoveryService`. |
| **Authoritative DNS Rate Limits** | Medium | Low | Cap maximum dictionary probes at 8. Utilize standard caching if analyzing domains in bulk. |
| **Provider Footprint Drift** | Medium | Low | Maintain Fingerprint Catalog as a discrete JSON/YAML config, isolated from core logic, allowing instant updates. |
| **False Negatives on Obscure Providers** | Low | Medium | Expose an override parameter in the API/CLI allowing the user to explicitly pass a custom selector if auto-discovery fails. |

---

## 7. Migration Plan

*Execution will commence after the prototype evaluation milestone.*

1. **Schema & Config:** Extract Provider Fingerprints and Dictionary Catalog into a configurable schema/JSON file.
2. **Component Creation:** Implement `DKIMDiscoveryService` to handle context gathering and prioritized selector listing.
3. **Orchestrator Update:** Modify `IntelligenceOrchestrator` to initialize the Discovery Service, retrieve the candidate list, and iterate against `DKIMValidator`.
4. **Validator Interface (Optional):** Keep `DKIMValidator` decoupled; it continues evaluating one selector at a time, allowing the Orchestrator to handle iteration and short-circuit logic.
5. **Dynamic Insights Update:** Update `engine.py` and `recommendations.py` to accept the inferred provider context to enrich `DKIM-001` remediation advice.
6. **M2F.4 Campaign:** Re-run the 28-domain real-world validation matrix. Target metric: `DKIM-001` drops from 27/28 to < 5/28 (only hitting domains truly lacking DKIM).
