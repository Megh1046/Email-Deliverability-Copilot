# Confidence Model

**Document ID:** DKB-006  
**Version:** 1.1  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026

---

## Purpose

The Deliverability Confidence Score (DCS) is the single output metric that summarizes the overall email authentication health of a domain. It powers the dashboard health indicator, report summaries, and the AI assistant's opening statement.

---

## Algorithm Overview

```
DCS = BASE_SCORE - SUM(deductions for active failing insights) + SUM(bonuses for active passing insights)

Minimum: 0
Maximum: 100
```

### Base Score
Every domain starts at **100** (perfect configuration assumed).

### Deductions
Every active **failing** insight (`positive = false`) applies its `confidence_weight` as a deduction.

**Double Counting Prevention Rule:** Cross-protocol insights may influence recommendations and severity but should not automatically create additional score deductions when the underlying protocol failures are already contributing to the score.

### Bonuses
Every active **passing** insight (`positive = true`) applies its `confidence_weight` as an addition.

### Floor and Ceiling
The score is clamped between 0 and 100 regardless of the calculation result.

---

## Scoring Bands

| Band | Score Range | Label | Color |
|---|---|---|---|
| EXCELLENT | 90 – 100 | ✅ Excellent | `#22c55e` (green) |
| GOOD | 75 – 89 | 🟢 Good | `#84cc16` (lime) |
| AT_RISK | 50 – 74 | 🟡 At Risk | `#eab308` (yellow) |
| POOR | 25 – 49 | 🔴 Poor | `#f97316` (orange) |
| CRITICAL | 0 – 24 | 🚨 Critical | `#ef4444` (red) |

---

## Severity Weight Table

### Deduction Weights (Failing Insights)

| Severity | Confidence Weight |
|---|---|
| CRITICAL | -20 |
| HIGH | -12 |
| MEDIUM | -6 |
| LOW | -2 |
| INFO | 0 |

### Bonus Weights (Passing Insights)

| Insight ID | Signal | Bonus Weight |
|---|---|---|
| XPRO-012 | All protocols pass and aligned | +10 |
| DMARC-017 | DMARC `p=reject` confirmed | +10 |
| (implicit) | DKIM key ≥ 2048 bits confirmed | +5 |
| (implicit) | SPF `-all` with ≤ 5 lookups | +5 |
| (implicit) | PTR / reverse DNS confirmed | +3 |
| (implicit) | DMARC `rua=` configured and reachable | +3 |

---

## Insight Weight Catalog

Full table of all defined insights and their confidence weights:

### DNS Insights

| Insight ID | Title | Weight |
|---|---|---|
| DNS-001 | No MX Record Found | -20 |
| DNS-002 | MX Record Points to IP Address | -12 |
| DNS-003 | Multiple Conflicting MX Records | -12 |
| DNS-004 | Missing PTR / Reverse DNS Record | -12 |
| DNS-005 | Missing A Record for Root Domain | -6 |
| DNS-006 | CNAME at Root Domain | -12 |
| DNS-007 | No NS Records Resolvable | -20 |
| DNS-008 | Domain NX — Non-Existent Domain | -20 |
| DNS-009 | Low TTL on MX Records | -2 |
| DNS-010 | MX Record Priority Misconfiguration | -2 |
| DNS-011 | SOA Record Missing or Malformed | -6 |
| DNS-012 | Excessive DNS Propagation Delay | -6 |

### SPF Insights

| Insight ID | Title | Weight |
|---|---|---|
| SPF-001 | No SPF Record Found | -20 |
| SPF-002 | Multiple SPF Records | -20 |
| SPF-003 | SPF Version Missing or Incorrect | -20 |
| SPF-004 | SPF Record Contains Syntax Error | -20 |
| SPF-005 | SPF Ends with `+all` | -20 |
| SPF-006 | SPF Has No `all` Mechanism | -12 |
| SPF-007 | SPF Ends with `?all` | -12 |
| SPF-008 | SPF Lookup Limit Exceeded | -12 |
| SPF-009 | `include:` Domain Does Not Exist | -12 |
| SPF-010 | `include:` Domain Has No SPF | -12 |
| SPF-011 | SPF Record Too Long | -6 |
| SPF-012 | SPF Uses Deprecated `ptr` | -6 |
| SPF-013 | SPF Lookup Approaching Limit | -6 |
| SPF-014 | `redirect=` and `all` Used Together | -12 |
| SPF-015 | Duplicate Mechanisms | -2 |
| SPF-016 | Redundant `ip4` Ranges | -2 |
| SPF-017 | Unknown Modifier | 0 |

### DKIM Insights

| Insight ID | Title | Weight |
|---|---|---|
| DKIM-001 | No DKIM Record for Selector | -20 |
| DKIM-002 | DKIM Public Key Missing | -20 |
| DKIM-003 | DKIM Record Missing `p=` Tag | -20 |
| DKIM-004 | DKIM Key Revoked | -20 |
| DKIM-005 | DKIM Record Not Parseable | -20 |
| DKIM-006 | DKIM Key Too Short (< 1024 bits) | -20 |
| DKIM-007 | DKIM Key Exactly 1024 bits | -12 |
| DKIM-008 | DKIM Version Tag Incorrect | -12 |
| DKIM-009 | DKIM `h=` SHA-1 Only | -12 |
| DKIM-010 | Multiple DKIM Records for Selector | -12 |
| DKIM-011 | DKIM Base64 Encoding Invalid | -12 |
| DKIM-012 | DKIM Unknown or Invalid Tags | -6 |
| DKIM-013 | DKIM Duplicate Tags | -6 |
| DKIM-014 | DKIM `s=` Restricts Service Type | -6 |
| DKIM-015 | DKIM `t=y` Testing Mode in Production | -6 |
| DKIM-016 | DKIM `t=s` Strict Subdomaining | -2 |
| DKIM-017 | DKIM `k=` Not Specified | -2 |

### DMARC Insights

| Insight ID | Title | Weight |
|---|---|---|
| DMARC-001 | No DMARC Record | -20 |
| DMARC-002 | DMARC Missing Version Tag | -20 |
| DMARC-003 | DMARC Syntax Error | -20 |
| DMARC-004 | Multiple DMARC Records | -20 |
| DMARC-005 | DMARC `p=none` | -15 |
| DMARC-006 | DMARC Missing `rua=` | -12 |
| DMARC-007 | DMARC `rua=` Not Authorized | -12 |
| DMARC-008 | DMARC `adkim=` Not Strict | -6 |
| DMARC-009 | DMARC `aspf=` Not Strict | -6 |
| DMARC-010 | DMARC `p=quarantine` | 0 |
| DMARC-011 | DMARC `pct=` Below 100% | -6 |
| DMARC-012 | DMARC Missing `sp=` | -6 |
| DMARC-013 | DMARC Duplicate Tags | -6 |
| DMARC-014 | DMARC Missing `ruf=` | -2 |
| DMARC-015 | DMARC `fo=` Not Set | -2 |
| DMARC-016 | DMARC `ri=` Too High | 0 |
| DMARC-017 | DMARC `p=reject` (Healthy) | +10 |

### Cross-Protocol Insights

| Insight ID | Title | Weight |
|---|---|---|
| XPRO-001 | No Authentication at All | -20 |
| XPRO-002 | Orphaned DMARC | -20 |
| XPRO-003 | SPF+DKIM Pass, DMARC Alignment Fails | -12 |
| XPRO-004 | DMARC Reject + SPF `+all` | -12 |
| XPRO-005 | DKIM Selector Unknown + DMARC Reject | -12 |
| XPRO-006 | SPF Softfail + DMARC Quarantine | -12 |
| XPRO-007 | No PTR + SPF Fail | -12 |
| XPRO-008 | Subdomain Not Covered + DMARC `sp=none` | -6 |
| XPRO-009 | DMARC `rua=` Domain Has No MX | -6 |
| XPRO-010 | DMARC Reject + SPF Near Limit | -6 |
| XPRO-011 | SPF Pass + DKIM Fail | -6 |
| XPRO-012 | Full Authentication Pass (Healthy) | +10 |

---

## Score Calculation Examples

### Example 1: Zero Authentication Domain

Active insights: XPRO-001 (-20), SPF-001 (-20), DKIM-001 (-20), DMARC-001 (-20)

Due to double-counting prevention, since XPRO-001 already accounts for the lack of authentication, the individual missing insights (-20 each) are suppressed from the score deduction calculation, OR XPRO-001 is suppressed while individual protocols apply. Assuming protocols sum together. Wait, if XPRO-001 does not stack:

```
DCS = 100 - 20 (SPF) - 20 (DKIM) - 20 (DMARC) = 40 (XPRO-001 suppressed from score to prevent stacking)
OR
DCS = 100 - 20 (XPRO-001) - 20 (other factors if any)
Band: POOR 🔴
```

*(Note: XPRO-001 supersedes individual protocol missing insights in presentation, and duplicate deductions are skipped per the prevention rule.)*

---

### Example 2: SPF Only, No DKIM, DMARC None

Active: DKIM-001 (-20), DMARC-005 (-15), DMARC-006 (-12), XPRO-011 (-6)

```
DCS = 100 - 20 - 15 - 12 - 6 = 47
Band: POOR 🔴
```

---

### Example 3: All Protocols Configured — SPF Lookup Approaching Limit

Active: SPF-013 (-6), DMARC-010 (0) [quarantine, not reject]  
Bonuses: none (not yet at reject)

```
DCS = 100 - 6 - 0 = 94
Band: EXCELLENT ✅
```

---

### Example 4: Fully Optimized Domain

Active failing insights: none  
Active passing: XPRO-012 (+10), DMARC-017 (+10), DKIM 2048-bit (+5), SPF `-all` ≤5 lookups (+5), PTR confirmed (+3), `rua=` reachable (+3)

```
DCS = 100 + 10 + 10 + 5 + 5 + 3 + 3 = 100 (clamped)
Band: EXCELLENT ✅
```

---

## Implementation Notes

- Deductions are **additive** — multiple insights stack.
- Cross-protocol insights stack on top of individual protocol insights, EXCEPT when they describe the exact same underlying failure (double counting prevention).
- The calculation must be performed **after** all validators complete.
- The score is recalculated on every analysis run — it is not cached.
- Bonus insights only apply when the passing condition is explicitly confirmed, not merely when the failing insight is absent.
