# Cross-Protocol Insights

**Document ID:** DKB-005  
**Version:** 1.0  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026  
**Protocol:** CROSS_PROTOCOL  
**Total Insights:** 12

---

## Purpose

Cross-protocol insights capture behaviors that emerge from the **interaction** between DNS, SPF, DKIM, and DMARC. No single protocol validator can detect these — they require the outputs of all validators to be analyzed together.

---

## Summary Table

| ID | Title | Severity | Automation |
|---|---|---|---|
| XPRO-001 | No Authentication at All (All Protocols Absent) | CRITICAL | SEMI_AUTOMATIC |
| XPRO-002 | Orphaned DMARC (No SPF, No DKIM) | CRITICAL | SEMI_AUTOMATIC |
| XPRO-003 | SPF and DKIM Pass but DMARC Fails Alignment | HIGH | MANUAL |
| XPRO-004 | DMARC Reject + SPF `+all` (Conflicting Posture) | HIGH | SEMI_AUTOMATIC |
| XPRO-005 | DKIM Selector Unknown + DMARC Reject | HIGH | SEMI_AUTOMATIC |
| XPRO-006 | SPF Softfail + DMARC Quarantine | HIGH | SEMI_AUTOMATIC |
| XPRO-007 | No PTR Record + SPF Fail | HIGH | NOT_POSSIBLE |
| XPRO-008 | SPF Subdomain Not Covered + DMARC `sp=none` | MEDIUM | SEMI_AUTOMATIC |
| XPRO-009 | DMARC `rua=` Reporting Domain Has No MX | MEDIUM | SEMI_AUTOMATIC |
| XPRO-010 | DMARC Over-Restricted + SPF Near Lookup Limit | MEDIUM | MANUAL |
| XPRO-011 | SPF Pass + DKIM Fail (Partial Authentication) | MEDIUM | SEMI_AUTOMATIC |
| XPRO-012 | Full Authentication Pass (All Protocols Healthy) | INFO | N/A |

---

## XPRO-001 — No Authentication at All

**Title:** No Authentication at All — All Protocols Absent  
**Category:** Authentication  
**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC | **Positive:** false

### Condition
Domain has no SPF record, no DKIM record for any known selector, and no DMARC record.

### Detection Logic
SPF validator returns `exists = false`. DKIM validator returns no valid record. DMARC validator returns `exists = false`.

### Business Impact
The domain has zero email authentication. It will fail all authentication checks at major providers. Google and Yahoo reject unauthenticated bulk email. The domain is trivially spoofable for phishing attacks.

### Technical Explanation
Without SPF, DKIM, or DMARC, there is no mechanism for receiving servers to verify email authenticity. This is the worst possible email security posture.

### User Explanation
Your domain has no email security configured at all. Your emails are almost certainly being blocked or going to spam at major providers like Gmail and Outlook. Anyone on the internet can impersonate your email address.

### Recommendation
```
action        : Implement SPF, DKIM, and DMARC in order.
urgency       : IMMEDIATE
effort        : > 1 HOUR
step_by_step  :
  1. Publish an SPF record identifying your sending servers.
  2. Generate a DKIM key pair and configure signing on your mail server.
  3. Publish the DKIM public key at your selector domain.
  4. Publish a DMARC record starting with p=none and an rua= address.
  5. Monitor DMARC reports and escalate policy over time.
```

### Dependencies
SPF-001, DKIM-001, DMARC-001

### References
- RFC 7208, RFC 6376, RFC 7489

---

## XPRO-002 — Orphaned DMARC (No SPF, No DKIM)

**Title:** Orphaned DMARC — DMARC Exists but No SPF and No DKIM  
**Category:** Authentication  
**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC | **Positive:** false

### Condition
DMARC record exists but neither SPF nor DKIM is configured.

### Detection Logic
DMARC validator returns `exists = true`. SPF validator returns `exists = false`. No valid DKIM records found.

### Business Impact
DMARC requires at least one aligned authentication method (SPF or DKIM) to pass. Without both, every message fails DMARC. If `p=reject`, all email delivery fails.

### Technical Explanation
DMARC enforces policy only on messages that fail both SPF alignment and DKIM alignment. If neither mechanism is configured, all messages fail both, causing every email to be quarantined or rejected based on the `p=` value.

### User Explanation
You have the policy record in place, but you haven't set up the actual authentication methods it enforces. All your emails are failing authentication, which may be getting them blocked.

### Recommendation
```
action        : Implement SPF and DKIM to provide authentication methods for DMARC to enforce.
urgency       : IMMEDIATE
effort        : > 1 HOUR
step_by_step  :
  1. Publish an SPF record for your domain immediately.
  2. Generate and publish a DKIM key pair.
  3. Verify SPF and DKIM pass before escalating DMARC policy.
```

### Dependencies
SPF-001, DKIM-001

### References
- RFC 7489 — Section 4.1

---

## XPRO-003 — SPF and DKIM Pass but DMARC Fails Alignment

**Title:** SPF and DKIM Pass but DMARC Fails Alignment  
**Category:** Alignment  
**Severity:** HIGH | **Weight:** -15 | **Automation:** MANUAL | **Positive:** false

### Condition
Both SPF and DKIM return pass, but DMARC alignment check fails for both.

### Detection Logic
SPF evaluator returns PASS. DKIM verifier returns valid signature. DMARC alignment check: SPF authenticated domain does not match From: domain AND DKIM `d=` does not match From: domain.

### Business Impact
DMARC requires alignment — the authenticated domain must match the From: header domain. Without alignment, DMARC fails even when SPF and DKIM individually pass. This is a common issue when using ESPs that send on behalf of the customer's domain.

### Technical Explanation
DMARC alignment (RFC 7489 §3.1): SPF alignment requires the RFC5321.MailFrom domain to match the RFC5322.From domain. DKIM alignment requires the `d=` in the DKIM signature to match the From: domain. Relaxed mode allows parent domain matching; strict requires exact match.

### User Explanation
Your emails are passing individual security checks, but the final policy check is failing because the "sender" domain and "from" domain don't match. This often happens when using email marketing services.

### Recommendation
```
action        : Align DKIM signing domain and SPF envelope sender with your From: domain.
urgency       : THIS_WEEK
effort        : 15–60 MIN
step_by_step  :
  1. Check the DKIM d= value in outbound email headers.
  2. Ensure your ESP signs with your domain (not their own).
  3. Check the Return-Path (envelope-from) domain matches your From: domain for SPF alignment.
  4. Configure DMARC adkim=r and aspf=r for relaxed alignment if using subdomains.
```

### Dependencies
SPF-001, DKIM-001, DMARC-001

### References
- RFC 7489 — Section 3.1 (Alignment)

---

## XPRO-004 — DMARC Reject + SPF `+all` (Conflicting Posture)

**Title:** DMARC `p=reject` with SPF `+all` — Conflicting Security Posture  
**Category:** Configuration  
**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC | **Positive:** false

### Condition
DMARC policy is `p=reject` or `p=quarantine`. SPF record ends with `+all`.

### Detection Logic
DMARC parser reads `p=` value as `reject` or `quarantine`. SPF parser identifies `+all` as the final mechanism.

### Business Impact
SPF `+all` authorizes all servers on the internet, nullifying SPF as a control. Meanwhile DMARC requires authentication. These two configurations are contradictory: DMARC enforces authentication while SPF grants universal permission. For senders not covered by other mechanisms, SPF passes for everyone, making DMARC enforcement weaker.

### Technical Explanation
With `+all`, SPF always returns PASS for any sender. This means DMARC's SPF alignment will pass for spoofed senders (as long as they align the From domain). The strict DMARC policy provides false confidence.

### User Explanation
You have a strict email policy but have accidentally left the door wide open for unauthorized senders via your SPF record. These two settings are contradicting each other.

### Recommendation
```
action        : Replace SPF `+all` with `-all` or `~all` immediately.
urgency       : IMMEDIATE
effort        : < 5 MIN
sample_record : v=spf1 include:_spf.google.com -all
```

### Dependencies
SPF-005, DMARC-001

### References
- RFC 7208, RFC 7489

---

## XPRO-005 — DKIM Selector Unknown + DMARC Reject

**Title:** DKIM Selector Not Found with DMARC `p=reject` Active  
**Category:** Authentication  
**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC | **Positive:** false

### Condition
No DKIM record found for the queried selector AND DMARC policy is `p=reject`.

### Detection Logic
DKIM validator returns NXDOMAIN for the selector. DMARC parser reads `p=reject`.

### Business Impact
With DMARC at `p=reject` and no DKIM, all email from the domain that cannot pass SPF alignment will be rejected. High risk of legitimate email delivery failure.

### Technical Explanation
DMARC `p=reject` requires at least one authentication mechanism to pass and align. If DKIM is absent and SPF alignment fails (e.g., when sending through an ESP), all email is rejected.

### User Explanation
You have your strictest email policy active, but your email signature isn't configured. Some or all of your legitimate emails may be getting blocked right now.

### Recommendation
```
action        : Urgently configure DKIM signing or temporarily reduce DMARC policy to p=quarantine while setting up DKIM.
urgency       : IMMEDIATE
effort        : 15–60 MIN
```

### Dependencies
DKIM-001, DMARC-001

### References
- RFC 6376, RFC 7489

---

## XPRO-006 — SPF Softfail + DMARC Quarantine

**Title:** SPF Softfail (`~all`) with DMARC `p=quarantine`  
**Category:** Deliverability  
**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC | **Positive:** false

### Condition
SPF record ends with `~all` (softfail) AND DMARC policy is `p=quarantine`.

### Detection Logic
SPF parser identifies `~all` as the final mechanism. DMARC parser reads `p=quarantine`.

### Business Impact
`~all` signals that senders not in the SPF record should be treated as suspect but not hard-failed. Combined with DMARC quarantine, unauthorized senders may still get messages through to the spam folder rather than being outright rejected. Upgrade to `-all` to close this gap.

### Technical Explanation
SPF softfail (`~all`) returns `SoftFail` for non-matching IPs. DMARC quarantine routes authentication failures to spam. Together they create a partially-enforced posture rather than a fully protective one.

### User Explanation
Your settings are partially protecting your domain. Upgrading SPF from "soft block" to "hard block" will better complement your quarantine policy.

### Recommendation
```
action        : Upgrade SPF from `~all` (softfail) to `-all` (hardfail) if all legitimate senders are covered.
urgency       : THIS_MONTH
effort        : < 5 MIN
sample_record : v=spf1 include:_spf.google.com -all
```

### Dependencies
SPF-005, DMARC-001

### References
- RFC 7208, RFC 7489

---

## XPRO-007 — No PTR Record + SPF Fail

**Title:** Missing PTR Record Combined with SPF Failure  
**Category:** DNS Health  
**Severity:** HIGH | **Weight:** -15 | **Automation:** NOT_POSSIBLE | **Positive:** false

### Condition
No PTR record exists for the sending IP AND SPF returns fail or softfail.

### Detection Logic
Reverse DNS query returns NXDOMAIN. SPF evaluator returns FAIL or SOFTFAIL.

### Business Impact
This combination is one of the highest-confidence spam signals used by major providers. Gmail's spam filter specifically penalizes the absence of PTR with SPF failure. Delivery rates drop significantly.

### Technical Explanation
PTR + SPF failure together indicate the sending server is neither reverse-verified nor authorized. Most ISP spam filters weight these signals multiplicatively. The probability of inbox placement drops to near zero.

### User Explanation
Your sending server doesn't have a "verified address" AND your domain's permission list doesn't include it either. This is a serious spam signal that will cause most email providers to block your emails.

### Recommendation
```
action        : Fix SPF immediately by adding the sending server. Request PTR from your hosting provider.
urgency       : IMMEDIATE
effort        : 15–60 MIN (SPF) + > 1 HOUR (PTR via hosting provider)
step_by_step  :
  1. Add the sending server's IP to your SPF record (ip4: or ip6:).
  2. Separately, contact your hosting/IP provider to create a PTR record.
  3. Verify both are resolved before resuming email sending.
```

### Dependencies
DNS-004, SPF-001

### References
- RFC 1912, RFC 7208

---

## XPRO-008 — SPF Subdomain Not Covered + DMARC `sp=none`

**Title:** Subdomain Sending Not Covered by SPF with No DMARC Subdomain Policy  
**Category:** Configuration  
**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC | **Positive:** false

### Condition
Emails are observed from subdomains not covered by the root SPF record AND DMARC `sp=` is set to `none` or not configured.

### Detection Logic
SPF lookup on subdomain returns `neutral` or `none`. DMARC `sp=` tag is `none` or absent (defaulting to root `p=`).

### Business Impact
Subdomain emails from unprotected subdomains fail SPF and inherit a weak or absent DMARC subdomain policy. This is a spoofing avenue for subdomains like `hr.example.com` or `billing.example.com`.

### User Explanation
Emails from portions of your website domain (like `updates.yourdomain.com`) aren't protected by your security settings, making them targets for impersonation.

### Recommendation
```
action        : Publish SPF records for active subdomains and set DMARC `sp=reject`.
urgency       : THIS_WEEK
effort        : 5–15 MIN
sample_record for DMARC: v=DMARC1; p=quarantine; sp=reject; rua=mailto:dmarc@example.com
```

### Dependencies
SPF-001, DMARC-012

### References
- RFC 7208, RFC 7489

---

## XPRO-009 — DMARC `rua=` Reporting Domain Has No MX

**Title:** DMARC Reporting Destination Domain Has No MX Record  
**Category:** Reporting  
**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC | **Positive:** false

### Condition
The domain in the DMARC `rua=` mailto URI has no MX record.

### Detection Logic
DMARC parser extracts domain from `rua=` value. DNS lookup for MX on that domain returns empty answer.

### Business Impact
If the `rua=` email domain cannot receive email (no MX), DMARC aggregate reports will be silently dropped by sending mail servers. The domain is effectively operating blind with no reporting visibility.

### Technical Explanation
Receivers send DMARC aggregate reports to the `rua=` address via SMTP. If the destination domain has no MX record, those SMTP deliveries will fail. RFC 7489 does not require receivers to retry indefinitely — reports are simply lost.

### User Explanation
Your DMARC reports are being sent to an address that can't receive email. You're missing all your authentication reports.

### Recommendation
```
action        : Update `rua=` to point to an email address on a domain with a working MX record.
urgency       : THIS_WEEK
effort        : 5–15 MIN
```

### Dependencies
DNS-001, DMARC-006

### References
- RFC 7489 — Section 7.2

---

## XPRO-010 — DMARC Over-Restricted + SPF Near Lookup Limit

**Title:** DMARC `p=reject` with SPF Lookup Count Near Limit  
**Category:** Configuration  
**Severity:** MEDIUM | **Weight:** -8 | **Automation:** MANUAL | **Positive:** false

### Condition
DMARC policy is `p=reject` AND SPF lookup count is 8 or more.

### Detection Logic
DMARC parser reads `p=reject`. SPF evaluator counts lookups at 8, 9, or 10.

### Business Impact
If SPF crosses the 10-lookup limit (e.g., after adding a new ESP), SPF returns `permerror`, causing DMARC to fail. With `p=reject` active, legitimate email would immediately be rejected. This is a latent incident waiting to happen.

### Technical Explanation
`p=reject` + SPF permerror = rejected legitimate email. The proximity to the lookup limit means adding any new email tool will trigger this incident.

### User Explanation
You have your strictest email policy active, but you're close to breaking your email authorization record. Adding any new email tool could immediately cause your legitimate emails to be blocked.

### Recommendation
```
action        : Reduce SPF lookup count to ≤ 6 before adding any new email services.
urgency       : THIS_WEEK
effort        : 15–60 MIN
```

### Dependencies
SPF-008, SPF-013, DMARC-001

### References
- RFC 7208, RFC 7489

---

## XPRO-011 — SPF Pass + DKIM Fail (Partial Authentication)

**Title:** SPF Passes but DKIM Fails — Partial Authentication  
**Category:** Authentication  
**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC | **Positive:** false

### Condition
SPF evaluation returns PASS with alignment. DKIM verification fails or returns no signature.

### Detection Logic
SPF evaluator returns PASS. DKIM verifier returns FAIL, TEMPERROR, or NONE.

### Business Impact
DMARC may still pass if SPF alignment succeeds (email still delivered under relaxed DMARC). However, the domain is missing redundant authentication. If the ESP changes their sending infrastructure (breaking SPF IP coverage), there is no DKIM fallback and DMARC will fail.

### Technical Explanation
DMARC requires at least one aligned mechanism to pass. SPF-only pass with DKIM failure is fragile. Best practice requires both SPF and DKIM to pass independently.

### User Explanation
Your emails are getting through via one security method, but the other is broken. If the first one stops working, your emails will immediately start being blocked.

### Recommendation
```
action        : Investigate and fix DKIM configuration to enable redundant authentication.
urgency       : THIS_WEEK
effort        : 15–60 MIN
```

### Dependencies
DKIM-001, DMARC-001

### References
- RFC 6376, RFC 7489

---

## XPRO-012 — Full Authentication Pass (All Protocols Healthy)

**Title:** Full Authentication Pass — All Protocols Healthy  
**Category:** Authentication  
**Severity:** INFO | **Weight:** +10 (BONUS) | **Automation:** N/A | **Positive:** true

### Condition
SPF returns PASS with alignment. DKIM returns valid signature with alignment. DMARC is present with `p=quarantine` or `p=reject`. No critical or high issues detected across DNS, SPF, DKIM, or DMARC.

### Detection Logic
SPF: PASS + aligned. DKIM: valid signature + aligned. DMARC: exists + policy ≥ quarantine + pct=100. No CRITICAL or HIGH severity insights active.

### Business Impact
The domain is operating at best-practice email authentication posture. Inbox placement rates with all major providers are maximized. Domain spoofing risk is minimized.

### Technical Explanation
Full authentication represents the complete protection stack: SPF verifies the message envelope, DKIM verifies message integrity and identity, and DMARC enforces policy and provides reporting.

### User Explanation
Excellent — your email authentication is fully configured and healthy. Your emails have the best possible chance of reaching the inbox, and your domain is protected against impersonation.

### Recommendation
No action required. Continue monitoring DMARC aggregate reports to catch any future configuration drift.

### Dependencies
None

### References
- RFC 7208, RFC 6376, RFC 7489
