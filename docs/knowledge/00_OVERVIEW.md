# Deliverability Knowledge Base — Overview

**Document ID:** DKB-000  
**Version:** 1.0  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026  
**Owner:** Email Deliverability Copilot

---

## Purpose

This document defines the canonical structures, models, severity levels, confidence weights, automation levels, and taxonomy used throughout the entire Deliverability Knowledge Base (DKB).

Every insight document (`01_DNS_INSIGHTS.md` through `09_BUSINESS_INSIGHTS.md`) is subordinate to this specification. Any structural change must be made here first.

---

## Document Index

| File | Contents |
|---|---|
| `00_OVERVIEW.md` | This file — canonical structures and model definitions |
| `01_DNS_INSIGHTS.md` | DNS record insights (12 insights) |
| `02_SPF_INSIGHTS.md` | SPF record insights (17 insights) |
| `03_DKIM_INSIGHTS.md` | DKIM record insights (17 insights) |
| `04_DMARC_INSIGHTS.md` | DMARC record insights (17 insights) |
| `05_CROSS_PROTOCOL_INSIGHTS.md` | Cross-protocol interaction insights (12 insights) |
| `06_CONFIDENCE_MODEL.md` | Deliverability Confidence Score algorithm |
| `07_RECOMMENDATION_MODEL.md` | Recommendation structure and priority model |
| `08_AUTOMATION_MAPPING.md` | Insight → automation level mapping |
| `09_BUSINESS_INSIGHTS.md` | Business-language translations for marketing users |

---

## Insight Structure

Every insight in the knowledge base follows this canonical schema. All fields are required unless marked optional.

```
insight_id          : Unique identifier (e.g., SPF-001, DMARC-005)
title               : Short, human-readable title of the insight
category            : One of the canonical categories (see below)
protocol            : DNS | SPF | DKIM | DMARC | CROSS_PROTOCOL
severity            : CRITICAL | HIGH | MEDIUM | LOW | INFO
condition           : What observed state triggers this insight
detection_logic     : How the validator detects this condition (maps to code)
business_impact     : What this means for email deliverability in plain terms
technical_explanation : Full RFC-level explanation of the issue
user_explanation    : Non-technical explanation for marketing users
recommendation      : Structured object (see Recommendation Structure below)
automation_level    : AUTOMATIC | SEMI_AUTOMATIC | MANUAL | NOT_POSSIBLE
confidence_weight   : Integer contribution to Deliverability Confidence Score
positive            : true if this is a passing/healthy insight, false if failing
dependencies        : List of other insight IDs that must be evaluated first (optional)
references          : RFC numbers, external documentation links
```

---

## Severity Model

Five severity tiers apply to all insights. Severity reflects impact on email deliverability when the condition is active.

### CRITICAL

**Definition:** The issue will cause email delivery failure or complete authentication breakdown.  
**User Signal:** "Your emails are being rejected or marked as spam by most providers."  
**Confidence Impact:** `-25 points`  
**Examples:** No SPF record, DMARC missing, DKIM key revoked, no MX record.

---

### HIGH

**Definition:** The issue significantly degrades deliverability or creates an exploitable security gap.  
**User Signal:** "Your emails may be rejected by major inbox providers."  
**Confidence Impact:** `-15 points`  
**Examples:** SPF `+all` permissive policy, DMARC `p=none`, DKIM key < 1024 bits, missing PTR record.

---

### MEDIUM

**Definition:** The configuration is suboptimal and creates deliverability risk over time.  
**User Signal:** "Your configuration has weaknesses that could hurt your sender reputation."  
**Confidence Impact:** `-8 points`  
**Examples:** DMARC `pct < 100`, SPF approaching lookup limit, DKIM 1024-bit key, `adkim=relaxed`.

---

### LOW

**Definition:** A minor configuration issue or hygiene problem with limited immediate impact.  
**User Signal:** "A minor improvement is available to strengthen your configuration."  
**Confidence Impact:** `-3 points`  
**Examples:** Duplicate SPF mechanisms, low TTL on MX, DMARC `fo=` not configured.

---

### INFO

**Definition:** An informational observation. No issue present; may indicate a healthy or neutral state.  
**User Signal:** "Informational — no action required."  
**Confidence Impact:** `0 points`  
**Examples:** Full authentication pass, DMARC `p=reject` (healthy), `ri=` reporting interval noted.

---

## Confidence Weight Model

The Deliverability Confidence Score (DCS) starts at **100** and is modified by active insights.

### Deduction Table (Failing Insights)

| Severity | Weight |
|---|---|
| CRITICAL | -25 |
| HIGH | -15 |
| MEDIUM | -8 |
| LOW | -3 |
| INFO | 0 |

### Bonus Table (Passing / Healthy Insights)

Positive signals that add to the score when best-practice configurations are confirmed:

| Signal | Weight |
|---|---|
| DMARC `p=reject` confirmed | +10 |
| DKIM key ≥ 2048 bits confirmed | +5 |
| SPF strict `~all` or `-all` with ≤ 5 lookups | +5 |
| All three protocols authenticated and aligned | +10 |
| PTR / reverse DNS record confirmed | +3 |
| DMARC aggregate reporting (`rua`) configured | +3 |

### Scoring Bands

| Band | Score Range | Label |
|---|---|---|
| EXCELLENT | 90 – 100 | ✅ Excellent |
| GOOD | 75 – 89 | 🟢 Good |
| AT RISK | 50 – 74 | 🟡 At Risk |
| POOR | 25 – 49 | 🔴 Poor |
| CRITICAL | 0 – 24 | 🚨 Critical |

---

## Automation Levels

Every insight maps to one of four automation levels.

### AUTOMATIC

**Definition:** The system can generate and apply the DNS fix without user input, subject to Cloudflare API access.  
**User Experience:** One-click "Fix automatically" button.  
**Examples:** Generate and publish SPF record, create DMARC record at `p=none`.

---

### SEMI_AUTOMATIC

**Definition:** The system generates the exact DNS record. The user must apply it manually (copy-paste or via their DNS provider).  
**User Experience:** "Here is your DNS record — copy and apply it."  
**Examples:** Generate DKIM key pair, generate SPF `include:` additions, recommended DMARC upgrade.

---

### MANUAL

**Definition:** The fix requires user decision-making or action that the system cannot automate.  
**User Experience:** Step-by-step instructions provided.  
**Examples:** Choosing DMARC policy escalation path, reviewing third-party email senders.

---

### NOT_POSSIBLE

**Definition:** The system cannot remediate this issue. It requires action by a third party or is outside DNS control.  
**User Experience:** Explanation and guidance only.  
**Examples:** PTR / reverse DNS (requires action from hosting provider), ISP-level blocks.

---

## Category Taxonomy

| Category | Description |
|---|---|
| `DNS` | DNS record existence, structure, and resolution |
| `SPF` | Sender Policy Framework configuration |
| `DKIM` | DomainKeys Identified Mail configuration |
| `DMARC` | Domain-based Message Authentication configuration |
| `Authentication` | Overall authentication posture across protocols |
| `Alignment` | SPF/DKIM identifier alignment with From: domain |
| `DNS Health` | DNS infrastructure quality and propagation |
| `Deliverability` | Direct inbox placement and reputation signals |
| `Domain Reputation` | Sender reputation and IP reputation signals |
| `Configuration` | General record configuration hygiene |
| `Security` | Authentication used to prevent spoofing and phishing |
| `Reporting` | DMARC reporting configuration and visibility |

---

## Recommendation Structure

Every insight recommendation follows this schema:

```
action          : What the user needs to do (imperative sentence)
urgency         : IMMEDIATE | THIS_WEEK | THIS_MONTH | WHEN_POSSIBLE
effort          : < 5 MIN | 5–15 MIN | 15–60 MIN | > 1 HOUR
impact          : HIGH | MEDIUM | LOW (impact on deliverability if fixed)
sample_record   : Example DNS record value (where applicable, optional)
step_by_step    : Ordered list of implementation steps
validation_cmd  : DNS query to confirm the fix is applied (optional)
```

---

## Insight ID Namespace

| Protocol | ID Prefix | Range |
|---|---|---|
| DNS | `DNS-` | DNS-001 through DNS-099 |
| SPF | `SPF-` | SPF-001 through SPF-099 |
| DKIM | `DKIM-` | DKIM-001 through DKIM-099 |
| DMARC | `DMARC-` | DMARC-001 through DMARC-099 |
| Cross-Protocol | `XPRO-` | XPRO-001 through XPRO-099 |
| Business | `BIZ-` | BIZ-001 through BIZ-099 |

---

## References

- RFC 1035 — Domain Names: Implementation and Specification  
- RFC 7208 — Sender Policy Framework (SPF)  
- RFC 6376 — DomainKeys Identified Mail (DKIM)  
- RFC 7489 — Domain-based Message Authentication, Reporting, and Conformance (DMARC)  
- RFC 8301 — Cryptographic Algorithm and Key Usage Update to DKIM  
- RFC 5321 — Simple Mail Transfer Protocol (SMTP)  
