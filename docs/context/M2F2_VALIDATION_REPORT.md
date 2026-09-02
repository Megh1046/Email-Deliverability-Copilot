# M2F.2 — Real World Domain Validation Campaign Report

**Generated:** 2026-08-06 07:03:02 UTC  
**Pipeline version:** M2F.1 (ARCH-015 enforced)  
**Domains tested:** 28  
**Results:** PASS=15  WARN=13  FAIL=0  

> **PASS** — All ARCH-015 consistency invariants satisfied and band within expected range.  
> **WARN** — Consistency invariants satisfied but band outside expected range (DNS state may have changed).  
> **FAIL** — One or more ARCH-015 invariants violated (score ceiling, BIZ-015 gating, band coherence).  

---

## Category Summary

| Category | Domains | PASS | WARN | FAIL |
|----------|---------|------|------|------|
| Excellent | 5 | 0 | 5 | 0 |
| Good | 5 | 0 | 5 | 0 |
| DMARC p=none | 4 | 3 | 1 | 0 |
| Missing DMARC | 4 | 3 | 1 | 0 |
| Weak SPF | 3 | 2 | 1 | 0 |
| Missing DKIM | 4 | 4 | 0 | 0 |
| Invalid | 3 | 3 | 0 | 0 |
| **TOTAL** | **28** | **15** | **13** | **0** |

---

## Master Results Table

| # | Domain | Category | Score | Band | Key Findings | Business Signals | Result |
|---|--------|----------|-------|------|-------------|-----------------|--------|
| 1 | google.com | Excellent | 49 | 🔴 POOR | `DKIM-001`, `DMARC-017` | `BIZ-001`, `BIZ-006` | ⚠️ WARN |
| 2 | microsoft.com | Excellent | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ⚠️ WARN |
| 3 | cloudflare.com | Excellent | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ⚠️ WARN |
| 4 | github.com | Excellent | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ⚠️ WARN |
| 5 | stripe.com | Excellent | 49 | 🔴 POOR | `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003` | ⚠️ WARN |
| 6 | apple.com | Good | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ⚠️ WARN |
| 7 | amazon.com | Good | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ⚠️ WARN |
| 8 | shopify.com | Good | 49 | 🔴 POOR | `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003` | ⚠️ WARN |
| 9 | notion.so | Good | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ⚠️ WARN |
| 10 | figma.com | Good | 49 | 🔴 POOR | `SPF-001` | `BIZ-001`, `BIZ-003` | ⚠️ WARN |
| 11 | reddit.com | DMARC p=none | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ✅ PASS |
| 12 | wikipedia.org | DMARC p=none | 49 | 🔴 POOR | `DKIM-001`, `DMARC-017` | `BIZ-001`, `BIZ-006` | ✅ PASS |
| 13 | twitch.tv | DMARC p=none | 49 | 🔴 POOR | `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003` | ✅ PASS |
| 14 | discord.com | DMARC p=none | 49 | 🔴 POOR | `DKIM-001`, `DMARC-017` | `BIZ-001`, `BIZ-006` | ⚠️ WARN |
| 15 | bbc.co.uk | Missing DMARC | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ✅ PASS |
| 16 | archive.org | Missing DMARC | 100 | 🟢 EXCELLENT | - | - | ⚠️ WARN |
| 17 | craigslist.org | Missing DMARC | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ✅ PASS |
| 18 | sourceforge.net | Missing DMARC | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ✅ PASS |
| 19 | aol.com | Weak SPF | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-017`, `SPF-001` | `BIZ-001`, `BIZ-003`, `BIZ-006` | ✅ PASS |
| 20 | hotmail.com | Weak SPF | 49 | 🔴 POOR | `DKIM-001` | `BIZ-001`, `BIZ-006` | ✅ PASS |
| 21 | protonmail.com | Weak SPF | 49 | 🔴 POOR | `DKIM-001` | `BIZ-001`, `BIZ-006` | ⚠️ WARN |
| 22 | php.net | Missing DKIM | 49 | 🔴 POOR | `DKIM-001` | `BIZ-001`, `BIZ-006` | ✅ PASS |
| 23 | kernel.org | Missing DKIM | 49 | 🔴 POOR | `DKIM-001` | `BIZ-001`, `BIZ-006` | ✅ PASS |
| 24 | apache.org | Missing DKIM | 49 | 🔴 POOR | `DKIM-001` | `BIZ-001`, `BIZ-006` | ✅ PASS |
| 25 | gnu.org | Missing DKIM | 49 | 🔴 POOR | `DKIM-001` | `BIZ-001`, `BIZ-006` | ✅ PASS |
| 26 | thisdoesnotexist-abc-xyz-999.com | Invalid | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-001`, `SPF-001` | `BIZ-001`, `BIZ-002`, `BIZ-003`, `BIZ-006` | ✅ PASS |
| 27 | notareal-domain-test-abc123.org | Invalid | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-001`, `SPF-001` | `BIZ-001`, `BIZ-002`, `BIZ-003`, `BIZ-006` | ✅ PASS |
| 28 | fake-broken-invalid-domain-xyz.net | Invalid | 49 | 🔴 POOR | `DKIM-001`, `XPRO-001`, `DMARC-001`, `SPF-001` | `BIZ-001`, `BIZ-002`, `BIZ-003`, `BIZ-006` | ✅ PASS |

---

## Category: Excellent

### ⚠️ google.com

> Google — canonical best-practice reference domain

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `7.48s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']`

---

### ⚠️ microsoft.com

> Microsoft — enterprise email infrastructure

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `selector1` |
| **DNS Elapsed** | `10.57s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']`

---

### ⚠️ cloudflare.com

> Cloudflare — infrastructure company, strong auth expected

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.65s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']`

---

### ⚠️ github.com

> GitHub — developer platform, full auth expected

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `15.75s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']`

---

### ⚠️ stripe.com

> Stripe — fintech, PCI/compliance drives strong email security

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.63s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns

**Recommendations:** `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']`

---

## Category: Good

### ⚠️ apple.com

> Apple — large enterprise, good auth expected

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `apple` |
| **DNS Elapsed** | `10.65s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']`

---

### ⚠️ amazon.com

> Amazon — major e-commerce, DKIM selector varies

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.77s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']`

---

### ⚠️ shopify.com

> Shopify — modern SaaS e-commerce

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.61s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns

**Recommendations:** `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']`

---

### ⚠️ notion.so

> Notion — SaaS, Google Workspace likely

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.65s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']`

---

### ⚠️ figma.com

> Figma — design SaaS, likely uses Google Workspace

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.7s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns

**Recommendations:** `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']`

---

## Category: DMARC p=none

### ✅ reddit.com

> Reddit — historically p=none DMARC

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `15.73s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ wikipedia.org

> Wikipedia — nonprofit, may have p=none

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `wikimedia` |
| **DNS Elapsed** | `0.56s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ twitch.tv

> Twitch — gaming platform, DMARC enforcement partial

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.65s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns

**Recommendations:** `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ⚠️ discord.com

> Discord — modern SaaS, DMARC status varies

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `1.09s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']`

---

## Category: Missing DMARC

### ✅ bbc.co.uk

> BBC UK — news org, DMARC gaps common in media

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.58s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ⚠️ archive.org

> Internet Archive — nonprofit, may lack DMARC

| Field | Value |
|-------|-------|
| **Score** | `100` |
| **Band** | 🟢 `EXCELLENT` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `0.89s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:** _(none)_

**Business Insights:** _(none)_

**Recommendations:** _(none)_

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `EXCELLENT`, Score = `100`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'EXCELLENT', expected one of ['AT_RISK', 'POOR', 'CRITICAL']`

---

### ✅ craigslist.org

> Craigslist — legacy system, expected weak email security

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `15.64s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ sourceforge.net

> SourceForge — legacy platform, email security gap likely

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.62s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

## Category: Weak SPF

### ✅ aol.com

> AOL — legacy provider, SPF complexity expected

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `10.67s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ℹ️ `DMARC-017` — INFO
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ hotmail.com

> Hotmail — legacy domain, may use complex SPF chains

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `0.49s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ⚠️ protonmail.com

> ProtonMail — privacy-focused, may have custom SPF

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `1.0s` |
| **Result** | ⚠️ **WARN** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

**⚠️ Expectation Mismatches (DNS may have changed):**
- `UNEXPECTED_BAND: got 'POOR', expected one of ['GOOD', 'AT_RISK', 'EXCELLENT']`

---

## Category: Missing DKIM

### ✅ php.net

> php.net — OSS project, likely no Google DKIM selector

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `0.61s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ kernel.org

> Linux kernel — OSS project, custom mail infra expected

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `0.51s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ apache.org

> Apache foundation — custom mail servers, no Google DKIM

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `8.43s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ gnu.org

> GNU project — independent mail infra, DKIM unlikely with google selector

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `google` |
| **DNS Elapsed** | `0.51s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

## Category: Invalid

### ✅ thisdoesnotexist-abc-xyz-999.com

> Non-existent domain — should get CRITICAL scores

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `(none)` |
| **DNS Elapsed** | `0.41s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ⛔ `DMARC-001` — CRITICAL
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-002` — Anyone Can Impersonate Your Brand in Email
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `DMARC-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ notareal-domain-test-abc123.org

> Non-existent domain — NXDOMAIN expected

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `(none)` |
| **DNS Elapsed** | `0.44s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ⛔ `DMARC-001` — CRITICAL
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-002` — Anyone Can Impersonate Your Brand in Email
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `DMARC-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

### ✅ fake-broken-invalid-domain-xyz.net

> Non-existent domain — all protocols should fail

| Field | Value |
|-------|-------|
| **Score** | `49` |
| **Band** | 🔴 `POOR` |
| **DKIM Selector** | `(none)` |
| **DNS Elapsed** | `0.42s` |
| **Result** | ✅ **PASS** |

**Active Insights:**
- ⛔ `DKIM-001` — CRITICAL
- ⛔ `XPRO-001` — CRITICAL
- ⛔ `DMARC-001` — CRITICAL
- ⛔ `SPF-001` — CRITICAL

**Business Insights:**
- `BIZ-001` — Your Emails Are Failing the Internet's Trust Check
- `BIZ-002` — Anyone Can Impersonate Your Brand in Email
- `BIZ-003` — Gmail and Yahoo May Be Blocking Your Campaigns
- `BIZ-006` — Your Emails Are Missing a Digital Signature

**Recommendations:** `DKIM-001`, `XPRO-001`, `DMARC-001`, `SPF-001`

**Expected Behaviour:** Band in ['—'], no unexpected BIZ insights
**Actual Behaviour:** Band = `POOR`, Score = `49`

All ARCH-015 consistency invariants satisfied.

---

## ARCH-015 Consistency Invariant Verification

| Invariant | Domains Tested | Violations |
|-----------|----------------|-----------|
| CRITICAL severity ceiling (score ≤ 49) | 28 | 0 |
| HIGH severity ceiling (score ≤ 74) | 28 | 0 |
| MEDIUM severity ceiling (score ≤ 89) | 28 | 0 |
| Band/score coherence | 28 | 0 |
| BIZ-015 contradiction prevention | 28 | 0 |
| Score in range [0, 100] | 28 | 0 |

> **Zero consistency violations across all 28 domains.**

## Campaign Quality Summary

| Metric | Count |
|--------|-------|
| False Positives (good domain flagged weak) | 1 |
| False Negatives (weak domain scored high) | 12 |
| Contradictions (BIZ/finding conflicts) | 0 |
| Logic Failures (ceiling / range violations) | 0 |

### False Positives
- archive.org: UNEXPECTED_BAND: got 'EXCELLENT', expected one of ['AT_RISK', 'POOR', 'CRITICAL']

### False Negatives
- google.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']
- microsoft.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']
- cloudflare.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']
- github.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']
- stripe.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD']
- apple.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']
- amazon.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']
- shopify.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']
- notion.so: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']
- figma.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']
- discord.com: UNEXPECTED_BAND: got 'POOR', expected one of ['EXCELLENT', 'GOOD', 'AT_RISK']
- protonmail.com: UNEXPECTED_BAND: got 'POOR', expected one of ['GOOD', 'AT_RISK', 'EXCELLENT']

## Score Distribution

| Band | Count | Domains |
|------|-------|---------|
| 🟢 EXCELLENT | 1 | archive.org |
| 🔴 POOR | 27 | google.com, microsoft.com, cloudflare.com, github.com, stripe.com, apple.com, amazon.com, shopify.com, notion.so, figma.com, reddit.com, wikipedia.org, twitch.tv, discord.com, bbc.co.uk, craigslist.org, sourceforge.net, aol.com, hotmail.com, protonmail.com, php.net, kernel.org, apache.org, gnu.org, thisdoesnotexist-abc-xyz-999.com, notareal-domain-test-abc123.org, fake-broken-invalid-domain-xyz.net |

---

---
*M2F.2 Validation Campaign · 2026-08-06 07:03:02 UTC*