# Automation Mapping

**Document ID:** DKB-008  
**Version:** 1.0  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026

---

## Purpose

This document maps every insight in the Deliverability Knowledge Base to its automation level and describes the specific automation action available. It is the primary reference for the Automation Engine.

---

## Automation Level Definitions

### AUTOMATIC
The system can generate and apply the DNS fix to the user's DNS provider (Cloudflare) without requiring user approval beyond an initial access grant. Triggered by the user clicking "Fix automatically."

**Cloudflare API required.** Action is logged and reversible.

---

### SEMI_AUTOMATIC
The system generates the exact DNS record value. The user must apply it manually via their DNS provider's control panel. The system provides the record in copy-paste-ready format and step-by-step instructions.

**No DNS API required.** Best for users on non-Cloudflare providers.

---

### MANUAL
The fix requires user decision-making, external research, or multi-step configuration that varies per environment. The system provides guidance and instructions but cannot generate a definitive record.

**No automation available.** Wizard-guided only.

---

### NOT_POSSIBLE
The fix requires action by a third party (hosting provider, ISP, registrar) or is outside the domain owner's control. The system explains the issue and who to contact.

**Neither automation nor self-service is possible.**

---

## Full Automation Mapping Table

### DNS Insights

| Insight ID | Title | Automation Level | Automation Action |
|---|---|---|---|
| DNS-001 | No MX Record Found | SEMI_AUTOMATIC | Generate MX record value for user's mail provider |
| DNS-002 | MX Points to IP Address | SEMI_AUTOMATIC | Generate correct MX + A record pair |
| DNS-003 | Multiple Conflicting MX Records | MANUAL | Guide user to identify correct provider and remove extras |
| DNS-004 | Missing PTR Record | NOT_POSSIBLE | Instructions to contact hosting/IP provider |
| DNS-005 | Missing A Record | SEMI_AUTOMATIC | Generate A record for root domain |
| DNS-006 | CNAME at Root Domain | SEMI_AUTOMATIC | Generate replacement A record |
| DNS-007 | No NS Records Resolvable | NOT_POSSIBLE | Instructions to contact registrar or DNS host |
| DNS-008 | Domain NX | NOT_POSSIBLE | Instructions to register or renew domain |
| DNS-009 | Low TTL on MX Records | SEMI_AUTOMATIC | Generate updated MX record with TTL=3600 |
| DNS-010 | MX Priority Misconfigured | SEMI_AUTOMATIC | Generate corrected MX records with proper priority |
| DNS-011 | SOA Missing or Malformed | NOT_POSSIBLE | Instructions to contact DNS hosting provider |
| DNS-012 | Excessive Propagation Delay | NOT_POSSIBLE | Monitoring guidance only |

---

### SPF Insights

| Insight ID | Title | Automation Level | Automation Action |
|---|---|---|---|
| SPF-001 | No SPF Record Found | SEMI_AUTOMATIC | Generate SPF record template based on detected mail services |
| SPF-002 | Multiple SPF Records | SEMI_AUTOMATIC | Generate merged single SPF record |
| SPF-003 | SPF Version Incorrect | SEMI_AUTOMATIC | Generate corrected SPF with proper v=spf1 |
| SPF-004 | SPF Syntax Error | SEMI_AUTOMATIC | Generate syntactically valid replacement SPF |
| SPF-005 | SPF `+all` | SEMI_AUTOMATIC | Generate corrected record with -all |
| SPF-006 | SPF No `all` | SEMI_AUTOMATIC | Generate record adding ~all |
| SPF-007 | SPF `?all` | SEMI_AUTOMATIC | Generate corrected record with ~all |
| SPF-008 | SPF Lookup Limit Exceeded | SEMI_AUTOMATIC | Generate optimized SPF with reduced lookup count |
| SPF-009 | `include:` Domain NXDOMAIN | MANUAL | Guide user to identify correct ESP include value |
| SPF-010 | `include:` Domain No SPF | MANUAL | Guide user to verify ESP's current SPF include |
| SPF-011 | SPF Record Too Long | SEMI_AUTOMATIC | Generate flattened SPF with ip4: consolidation |
| SPF-012 | SPF uses `ptr` | SEMI_AUTOMATIC | Generate record replacing ptr with ip4: ranges |
| SPF-013 | SPF Lookup Near Limit | SEMI_AUTOMATIC | Generate optimized SPF with reduced lookup count |
| SPF-014 | `redirect=` + `all` Together | SEMI_AUTOMATIC | Generate corrected record removing the conflict |
| SPF-015 | Duplicate Mechanisms | SEMI_AUTOMATIC | Generate deduplicated SPF record |
| SPF-016 | Redundant `ip4` Ranges | SEMI_AUTOMATIC | Generate consolidated CIDR SPF record |
| SPF-017 | Unknown Modifier | MANUAL | Guide user to review and correct |

---

### DKIM Insights

| Insight ID | Title | Automation Level | Automation Action |
|---|---|---|---|
| DKIM-001 | No DKIM Record | SEMI_AUTOMATIC | Guide user through key generation; generate TXT record template |
| DKIM-002 | DKIM Public Key Missing | SEMI_AUTOMATIC | Guide user to regenerate and republish key |
| DKIM-003 | DKIM Missing `p=` Tag | SEMI_AUTOMATIC | Generate corrected DKIM record with key field |
| DKIM-004 | DKIM Key Revoked | SEMI_AUTOMATIC | Guide through new key generation; generate TXT record |
| DKIM-005 | DKIM Not Parseable | SEMI_AUTOMATIC | Generate syntactically valid DKIM record template |
| DKIM-006 | DKIM Key < 1024 bits | SEMI_AUTOMATIC | Guide new 2048-bit key generation; generate record |
| DKIM-007 | DKIM Key 1024 bits | SEMI_AUTOMATIC | Guide new 2048-bit key generation; generate record |
| DKIM-008 | DKIM Version Incorrect | SEMI_AUTOMATIC | Generate corrected record with v=DKIM1 |
| DKIM-009 | DKIM `h=` SHA-1 Only | SEMI_AUTOMATIC | Generate corrected record with h=sha256 |
| DKIM-010 | Multiple DKIM Records | MANUAL | Guide user to identify active record and delete duplicates |
| DKIM-011 | DKIM Base64 Invalid | SEMI_AUTOMATIC | Guide key regeneration; generate corrected record |
| DKIM-012 | DKIM Unknown Tags | MANUAL | Guide user to review and remove unknown tags |
| DKIM-013 | DKIM Duplicate Tags | SEMI_AUTOMATIC | Generate deduplicated DKIM record |
| DKIM-014 | DKIM `s=` Restricts Service | SEMI_AUTOMATIC | Generate corrected record with s=email |
| DKIM-015 | DKIM `t=y` Testing Mode | SEMI_AUTOMATIC | Generate record with t=y removed |
| DKIM-016 | DKIM `t=s` Strict Subdomain | SEMI_AUTOMATIC | Generate corrected record with t=s removed |
| DKIM-017 | DKIM `k=` Not Specified | SEMI_AUTOMATIC | Generate record adding k=rsa |

---

### DMARC Insights

| Insight ID | Title | Automation Level | Automation Action |
|---|---|---|---|
| DMARC-001 | No DMARC Record | SEMI_AUTOMATIC | Generate DMARC record at p=none with rua= |
| DMARC-002 | DMARC Missing Version | SEMI_AUTOMATIC | Generate corrected record with v=DMARC1 |
| DMARC-003 | DMARC Syntax Error | SEMI_AUTOMATIC | Generate syntactically valid DMARC record |
| DMARC-004 | Multiple DMARC Records | SEMI_AUTOMATIC | Guide to delete extras; generate correct single record |
| DMARC-005 | DMARC `p=none` | SEMI_AUTOMATIC | Generate escalated record at p=quarantine |
| DMARC-006 | DMARC Missing `rua=` | SEMI_AUTOMATIC | Generate updated record adding rua= |
| DMARC-007 | DMARC `rua=` Not Authorized | MANUAL | Guide user to publish authorization record at external domain |
| DMARC-008 | DMARC `adkim=r` | SEMI_AUTOMATIC | Generate record with adkim=s |
| DMARC-009 | DMARC `aspf=r` | SEMI_AUTOMATIC | Generate record with aspf=s |
| DMARC-010 | DMARC `p=quarantine` | INFO | Informational — guide escalation path to p=reject |
| DMARC-011 | DMARC `pct=` < 100 | SEMI_AUTOMATIC | Generate record with pct=100 |
| DMARC-012 | DMARC Missing `sp=` | SEMI_AUTOMATIC | Generate record adding sp=reject |
| DMARC-013 | DMARC Duplicate Tags | SEMI_AUTOMATIC | Generate deduplicated DMARC record |
| DMARC-014 | DMARC Missing `ruf=` | SEMI_AUTOMATIC | Generate record adding ruf= |
| DMARC-015 | DMARC `fo=` Not Set | SEMI_AUTOMATIC | Generate record adding fo=1 |
| DMARC-016 | DMARC `ri=` Too High | SEMI_AUTOMATIC | Generate record with ri=86400 |
| DMARC-017 | DMARC `p=reject` (Healthy) | N/A | No action — positive signal |

---

### Cross-Protocol Insights

| Insight ID | Title | Automation Level | Automation Action |
|---|---|---|---|
| XPRO-001 | No Authentication at All | SEMI_AUTOMATIC | Sequence: generate SPF → guide DKIM → generate DMARC |
| XPRO-002 | Orphaned DMARC | SEMI_AUTOMATIC | Sequence: generate SPF → guide DKIM key generation |
| XPRO-003 | SPF+DKIM Pass, DMARC Fails Alignment | MANUAL | Guide user to configure ESP domain alignment |
| XPRO-004 | DMARC Reject + SPF `+all` | SEMI_AUTOMATIC | Generate corrected SPF with -all |
| XPRO-005 | DKIM Selector Unknown + DMARC Reject | SEMI_AUTOMATIC | Guide DKIM setup; generate key record |
| XPRO-006 | SPF Softfail + DMARC Quarantine | SEMI_AUTOMATIC | Generate SPF with -all |
| XPRO-007 | No PTR + SPF Fail | NOT_POSSIBLE (PTR) + SEMI_AUTOMATIC (SPF) | Fix SPF automatically; guide PTR request to hosting provider |
| XPRO-008 | Subdomain Not Covered + `sp=none` | SEMI_AUTOMATIC | Generate DMARC with sp=reject |
| XPRO-009 | DMARC `rua=` Domain No MX | SEMI_AUTOMATIC | Guide update of rua= to valid email domain |
| XPRO-010 | DMARC Reject + SPF Near Limit | MANUAL | Guide SPF consolidation |
| XPRO-011 | SPF Pass + DKIM Fail | SEMI_AUTOMATIC | Guide DKIM remediation |
| XPRO-012 | Full Authentication Pass | N/A | No action — positive signal |

---

## Cloudflare Automation Candidates

The following insights are candidates for **AUTOMATIC** execution via the Cloudflare DNS API (future Phase 3 automation):

| Insight ID | Record Operation | Cloudflare API Method |
|---|---|---|
| SPF-001 | Create TXT record | `POST /zones/:id/dns_records` |
| SPF-002 | Delete extras, create merged | DELETE + POST |
| SPF-005 | Update TXT record value | `PATCH /zones/:id/dns_records/:id` |
| SPF-006 | Update TXT record value | PATCH |
| DMARC-001 | Create TXT record at _dmarc | POST |
| DMARC-002 | Update TXT record value | PATCH |
| DMARC-005 | Update `p=` value | PATCH |
| DMARC-006 | Update record to add `rua=` | PATCH |
| DMARC-011 | Update `pct=` value | PATCH |
| DMARC-012 | Update record to add `sp=` | PATCH |
| DNS-001 | Create MX record | POST |

---

## User Confirmation Requirements

| Automation Level | User Action Required |
|---|---|
| AUTOMATIC | One-time Cloudflare API access grant. One-click "Apply Fix." |
| SEMI_AUTOMATIC | Copy generated record. Log in to DNS provider. Paste and save. |
| MANUAL | Follow wizard instructions. User makes all decisions and changes. |
| NOT_POSSIBLE | Contact third party. System provides contact instructions only. |
