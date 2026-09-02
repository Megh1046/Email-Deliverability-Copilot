# DMARC Insights

**Document ID:** DKB-004  
**Version:** 1.0  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026  
**Protocol:** DMARC  
**Total Insights:** 17

---

## Summary Table

| ID | Title | Severity | Automation |
|---|---|---|---|
| DMARC-001 | No DMARC Record Found | CRITICAL | SEMI_AUTOMATIC |
| DMARC-002 | DMARC Record Missing Version (`v=DMARC1`) | CRITICAL | SEMI_AUTOMATIC |
| DMARC-003 | DMARC Record Has Syntax Error | CRITICAL | SEMI_AUTOMATIC |
| DMARC-004 | Multiple DMARC Records Found | CRITICAL | SEMI_AUTOMATIC |
| DMARC-005 | DMARC Policy Set to None (`p=none`) | HIGH | SEMI_AUTOMATIC |
| DMARC-006 | DMARC Missing Aggregate Reporting URI (`rua=`) | HIGH | SEMI_AUTOMATIC |
| DMARC-007 | DMARC `rua=` URI Not Authorized (External Domain) | HIGH | MANUAL |
| DMARC-008 | DMARC `adkim=` Alignment Not Strict | MEDIUM | SEMI_AUTOMATIC |
| DMARC-009 | DMARC `aspf=` Alignment Not Strict | MEDIUM | SEMI_AUTOMATIC |
| DMARC-010 | DMARC Policy Set to Quarantine (`p=quarantine`) | MEDIUM | INFO |
| DMARC-011 | DMARC `pct=` Below 100% | MEDIUM | SEMI_AUTOMATIC |
| DMARC-012 | DMARC Missing Subdomain Policy (`sp=`) | MEDIUM | SEMI_AUTOMATIC |
| DMARC-013 | DMARC Record Has Duplicate Tags | MEDIUM | SEMI_AUTOMATIC |
| DMARC-014 | DMARC Missing Forensic Reporting URI (`ruf=`) | LOW | SEMI_AUTOMATIC |
| DMARC-015 | DMARC `fo=` Failure Reporting Options Not Set | LOW | SEMI_AUTOMATIC |
| DMARC-016 | DMARC `ri=` Reporting Interval Set Too High | INFO | SEMI_AUTOMATIC |
| DMARC-017 | DMARC Policy Set to Reject (`p=reject`) — Healthy | INFO | N/A |

---

## DMARC-001 — No DMARC Record Found

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
No DMARC TXT record exists at `_dmarc.<domain>`.

### Detection Logic
DNS resolver returns NXDOMAIN or no TXT answer for the `_dmarc.<domain>` query.

### Business Impact
Without DMARC, the domain has no policy governing email authentication failures. Domain spoofing is possible. Google, Yahoo, and other major providers require DMARC for bulk senders. Missing DMARC is a top barrier to inbox placement.

### Technical Explanation
RFC 7489 defines DMARC as a policy layer on top of SPF and DKIM. The policy record at `_dmarc.<domain>` tells receiving servers what to do when authentication fails (`none` / `quarantine` / `reject`). Without it, receivers cannot determine domain policy.

### User Explanation
Your domain has no email policy record. Email providers can't act on failed authentication checks, making your domain easy to impersonate. Google and Yahoo both require this record for reliable inbox delivery.

### Recommendation
```
action        : Publish a DMARC TXT record at _dmarc.<domain> starting with p=none.
urgency       : IMMEDIATE
effort        : 5–15 MIN
sample_record : v=DMARC1; p=none; rua=mailto:dmarc@example.com
step_by_step  :
  1. Log in to your DNS provider.
  2. Create a TXT record for the hostname: _dmarc
  3. Set value to: v=DMARC1; p=none; rua=mailto:<your_report_email>
  4. Save and verify with: dig TXT _dmarc.example.com
  5. Escalate policy to quarantine, then reject as you gain confidence.
validation_cmd: dig TXT _dmarc.example.com
```

### References
- RFC 7489 — DMARC  
- Google/Yahoo Sender Requirements (2024)

---

## DMARC-002 — DMARC Record Missing Version Tag

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
A TXT record exists at `_dmarc.<domain>` but does not begin with `v=DMARC1`.

### Detection Logic
DMARC parser finds TXT record at the DMARC path. First tag is not `v=DMARC1`.

### Technical Explanation
RFC 7489 §6.3 requires `v=DMARC1` as the first tag. Records not starting with this are invalid and ignored by receivers.

### User Explanation
Your DMARC record has a version error that causes email providers to ignore it entirely.

### Recommendation
```
action        : Ensure the DMARC record starts with exactly `v=DMARC1;`.
urgency       : IMMEDIATE
effort        : < 5 MIN
sample_record : v=DMARC1; p=none; rua=mailto:dmarc@example.com
validation_cmd: dig TXT _dmarc.example.com
```

### References
- RFC 7489 — Section 6.3

---

## DMARC-003 — DMARC Record Has Syntax Error

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record exists but fails to parse due to invalid tag values or malformed tag-value format.

### Detection Logic
DMARC parser encounters an invalid tag identifier, an unknown `p=` value, or a malformed tag-value structure.

### Technical Explanation
RFC 7489 defines strict grammar for DMARC records. Invalid `p=` values (not `none`/`quarantine`/`reject`), unknown tags, or format errors cause receivers to treat the record as invalid.

### User Explanation
Your DMARC record contains a typo or formatting error that email providers cannot read.

### Recommendation
```
action        : Validate and correct the DMARC record syntax.
urgency       : IMMEDIATE
effort        : 5–15 MIN
sample_record : v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com; pct=100
step_by_step  :
  1. Retrieve the current DMARC record.
  2. Use a DMARC validator to identify the exact error.
  3. Fix the syntax and republish.
validation_cmd: dig TXT _dmarc.example.com
```

### References
- RFC 7489 — Section 6.4

---

## DMARC-004 — Multiple DMARC Records Found

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
Two or more TXT records starting with `v=DMARC1` exist at `_dmarc.<domain>`.

### Detection Logic
DNS resolver returns multiple TXT records at the DMARC path.

### Technical Explanation
RFC 7489 §6.6.3 specifies that if multiple DMARC records are found, receivers must treat it as a permanent error and discard both. Similar to the multiple SPF records problem.

### User Explanation
You have two DMARC records when only one is allowed. Email providers discard both, leaving your domain with no policy.

### Recommendation
```
action        : Delete all DMARC records and republish a single correct one.
urgency       : IMMEDIATE
effort        : 5–15 MIN
step_by_step  :
  1. Identify all TXT records at _dmarc.<domain>.
  2. Delete all but the correct, intended record.
  3. Verify a single record remains.
validation_cmd: dig TXT _dmarc.example.com
```

### References
- RFC 7489 — Section 6.6.3

---

## DMARC-005 — DMARC Policy Set to None (`p=none`)

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record has `p=none`.

### Detection Logic
DMARC parser reads `p=` tag. Value is `none`.

### Business Impact
`p=none` is monitoring-only. No action is taken on authentication failures. Spoofed emails from your domain are delivered without quarantine or rejection. This is appropriate for initial deployment but must be escalated.

### Technical Explanation
`p=none` instructs receivers to take no action on authentication failures, only to send reports. It provides zero anti-spoofing protection. Google and Yahoo require at least `p=quarantine` for bulk senders.

### User Explanation
Your email policy is set to "watch only" mode. Email providers can see that emails from your domain fail checks, but they're not blocking them. This needs to be upgraded to protect your domain.

### Recommendation
```
action        : Escalate DMARC policy from `p=none` to `p=quarantine` after reviewing reports.
urgency       : THIS_MONTH
effort        : < 5 MIN
sample_record : v=DMARC1; p=quarantine; pct=25; rua=mailto:dmarc@example.com
step_by_step  :
  1. Review DMARC aggregate reports (rua) for 2–4 weeks.
  2. Confirm all legitimate senders pass SPF and DKIM.
  3. Change p=none to p=quarantine with pct=25 initially.
  4. Gradually increase pct to 100, then upgrade to p=reject.
validation_cmd: dig TXT _dmarc.example.com
```

### References
- RFC 7489 — Section 6.3 (`p=` tag)

---

## DMARC-006 — DMARC Missing Aggregate Reporting URI

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record does not contain an `rua=` tag.

### Detection Logic
DMARC parser processes tag list and finds no `rua=` tag.

### Business Impact
Without `rua=`, the domain receives no DMARC aggregate reports. This means there is no visibility into who is sending email from the domain or whether authentication is passing. Blind operation significantly increases breach risk.

### Technical Explanation
`rua=` specifies where receivers send aggregate XML reports summarizing authentication results. Without it, there is no feedback loop. Visibility into authentication posture is lost.

### User Explanation
You're not receiving any reports about your email authentication results. You have no way of knowing if your setup is working or if someone is impersonating your domain.

### Recommendation
```
action        : Add `rua=mailto:<report_email>` to your DMARC record.
urgency       : THIS_WEEK
effort        : < 5 MIN
sample_record : v=DMARC1; p=none; rua=mailto:dmarc@example.com
step_by_step  :
  1. Set up a dedicated email address or use a DMARC reporting service.
  2. Add rua=mailto:<address> to your DMARC record.
  3. Republish and confirm reports arrive within 24 hours.
```

### References
- RFC 7489 — Section 6.3 (`rua=` tag)

---

## DMARC-007 — DMARC `rua=` URI Not Authorized (External Domain)

**Severity:** HIGH | **Weight:** -15 | **Automation:** MANUAL

### Condition
The `rua=` URI points to an email address at a different domain than the DMARC-protected domain, and the external domain has not published a DMARC authorization record.

### Detection Logic
DMARC parser extracts the domain from the `rua=` mailto URI. If it differs from the protected domain, checks for `<protected_domain>._report._dmarc.<rua_domain>` TXT record. If absent, triggers the insight.

### Technical Explanation
RFC 7489 §7.1 requires that when reports are directed to external domains, the external domain must authorize receipt via a `<protected_domain>._report._dmarc.<external_domain>` TXT record. Without it, receivers will silently suppress reports.

### User Explanation
Your DMARC reports are being sent to a different domain, but that domain hasn't authorized receiving them. You may be missing all your authentication reports.

### Recommendation
```
action        : Publish an authorization record on the rua= destination domain.
urgency       : THIS_WEEK
effort        : 5–15 MIN
sample_record : example.com._report._dmarc.reportingservice.com. IN TXT "v=DMARC1"
step_by_step  :
  1. Confirm the rua= destination domain.
  2. Publish: <your_domain>._report._dmarc.<rua_domain> TXT "v=DMARC1"
  3. Verify with dig query on the authorization record.
```

### References
- RFC 7489 — Section 7.1

---

## DMARC-008 — DMARC `adkim=` Alignment Not Strict

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record has `adkim=r` (relaxed) or no `adkim=` tag (defaults to relaxed).

### Detection Logic
DMARC parser reads `adkim=` tag. Value is `r` or tag is absent.

### Business Impact
Relaxed DKIM alignment allows subdomains of the From: domain to satisfy DKIM alignment. Strict alignment (`adkim=s`) requires an exact domain match, providing stronger phishing protection.

### Technical Explanation
RFC 7489: relaxed mode (`r`) allows `d=` in DKIM signature to be a parent domain of the From: address. Strict mode (`s`) requires exact match. For high-security configurations, strict is recommended.

### User Explanation
Your DMARC is configured with looser signature matching rules. This is acceptable but upgrading to strict mode prevents more sophisticated spoofing attacks.

### Recommendation
```
action        : Consider upgrading `adkim=r` to `adkim=s` after validating all signing configurations.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
sample_record : v=DMARC1; p=quarantine; adkim=s; aspf=s; rua=mailto:dmarc@example.com
```

### References
- RFC 7489 — Section 6.3 (`adkim=` tag)

---

## DMARC-009 — DMARC `aspf=` Alignment Not Strict

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record has `aspf=r` (relaxed) or no `aspf=` tag.

### Detection Logic
DMARC parser reads `aspf=` tag. Value is `r` or tag absent (defaults to `r`).

### Technical Explanation
Same as DMARC-008 but for SPF alignment. Relaxed SPF alignment allows the SPF-authenticated domain to be a parent domain of the From: header address.

### User Explanation
Your DMARC uses looser email source matching rules for SPF. Upgrading to strict mode provides stronger protection against spoofing.

### Recommendation
```
action        : Consider upgrading `aspf=r` to `aspf=s` after validating SPF configuration.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
sample_record : v=DMARC1; p=quarantine; aspf=s; rua=mailto:dmarc@example.com
```

### References
- RFC 7489 — Section 6.3 (`aspf=` tag)

---

## DMARC-010 — DMARC Policy Set to Quarantine

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** INFO

### Condition
The DMARC record has `p=quarantine`.

### Detection Logic
DMARC parser reads `p=` tag. Value is `quarantine`.

### Business Impact
`p=quarantine` causes authentication failures to be routed to spam/junk folder rather than rejected. This is a significant improvement over `p=none` but does not provide full protection. Escalation to `p=reject` is recommended.

### Technical Explanation
Quarantine policy is a transitional state. It provides partial protection by routing failing messages to spam rather than delivering them to inbox. Full protection requires `p=reject`.

### User Explanation
Your email policy currently allows suspicious emails to be placed in spam folders rather than fully blocked. Consider upgrading to full block (`p=reject`) once you've confirmed your legitimate emails pass authentication.

### Recommendation
```
action        : Review DMARC reports and escalate to `p=reject` when confident all legitimate mail passes.
urgency       : THIS_MONTH
effort        : < 5 MIN
sample_record : v=DMARC1; p=reject; rua=mailto:dmarc@example.com
```

### References
- RFC 7489 — Section 6.3

---

## DMARC-011 — DMARC `pct=` Below 100%

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record contains `pct=` with a value less than 100.

### Detection Logic
DMARC parser reads `pct=` tag. Numeric value is below 100.

### Business Impact
A `pct=` below 100 means the DMARC policy applies to only a percentage of failing messages. The remaining percentage is treated as `p=none`. This is acceptable during rollout but must reach 100% for full enforcement.

### Technical Explanation
RFC 7489 §6.3: `pct=` controls the percentage of failing mail subject to the policy. Default is 100. A lower value is intended for phased rollout only.

### User Explanation
Your DMARC policy only applies to part of your email traffic. Some unauthorized emails are still slipping through.

### Recommendation
```
action        : Increase `pct=` to 100 once you've confirmed legitimate mail passes DMARC.
urgency       : THIS_MONTH
effort        : < 5 MIN
sample_record : v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@example.com
```

### References
- RFC 7489 — Section 6.3 (`pct=` tag)

---

## DMARC-012 — DMARC Missing Subdomain Policy

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record does not contain an `sp=` tag.

### Detection Logic
DMARC parser processes tag list. No `sp=` tag found.

### Business Impact
Without `sp=`, the subdomain policy inherits from the root domain `p=` value. If `p=none`, all subdomains also have no enforcement, leaving them vulnerable to spoofing. Subdomains (e.g., `mail.example.com`) are a common target for phishing.

### Technical Explanation
RFC 7489 §6.3: `sp=` defines the policy for subdomains. When absent, the root `p=` policy applies to subdomains. Explicitly setting `sp=reject` protects subdomains regardless of root policy transitions.

### User Explanation
Your email policy doesn't explicitly address your subdomains. Attackers can impersonate emails from `payments.yourdomain.com` or similar.

### Recommendation
```
action        : Add `sp=reject` to your DMARC record to protect all subdomains.
urgency       : THIS_WEEK
effort        : < 5 MIN
sample_record : v=DMARC1; p=quarantine; sp=reject; rua=mailto:dmarc@example.com
```

### References
- RFC 7489 — Section 6.3 (`sp=` tag)

---

## DMARC-013 — DMARC Record Has Duplicate Tags

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record contains the same tag name more than once.

### Detection Logic
DMARC parser builds a tag map and finds duplicate key entries.

### Technical Explanation
RFC 7489 §6.4 requires that tag names MUST NOT appear more than once. Duplicate tags make the record syntactically invalid. Policy is undefined when `p=` appears twice with different values.

### User Explanation
Your DMARC record lists the same field twice, creating ambiguity and potential policy failure.

### Recommendation
```
action        : Remove duplicate tags from the DMARC record.
urgency       : THIS_WEEK
effort        : < 5 MIN
```

### References
- RFC 7489 — Section 6.4

---

## DMARC-014 — DMARC Missing Forensic Reporting URI

**Severity:** LOW | **Weight:** -3 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record does not contain an `ruf=` tag.

### Detection Logic
DMARC parser finds no `ruf=` tag in the record.

### Business Impact
Without `ruf=`, no message-level failure reports are generated. These reports provide specific email sample data when authentication fails, enabling rapid debugging of configuration problems.

### Technical Explanation
`ruf=` specifies the URI for forensic (failure) reports: message-level reports sent when a specific message fails DMARC. Many providers have reduced forensic reporting due to privacy concerns, but the tag is still useful where supported.

### User Explanation
You're missing the setting that enables detailed reports about individual emails that fail your security checks. These help diagnose problems faster.

### Recommendation
```
action        : Add `ruf=mailto:<email>` to your DMARC record.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
sample_record : v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com; ruf=mailto:forensic@example.com
```

### References
- RFC 7489 — Section 6.3 (`ruf=` tag)

---

## DMARC-015 — DMARC `fo=` Failure Reporting Not Set

**Severity:** LOW | **Weight:** -3 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record does not contain an `fo=` tag.

### Detection Logic
DMARC parser finds no `fo=` tag.

### Technical Explanation
`fo=` controls when forensic reports are generated. Default is `0` (only when both SPF and DKIM fail). Setting `fo=1` generates reports when any authentication mechanism fails, providing more granular debugging information.

### User Explanation
Your DMARC reports are configured with the default minimal reporting. Adding specific reporting options gives you better visibility into authentication failures.

### Recommendation
```
action        : Add `fo=1` to get forensic reports on any individual authentication failure.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
sample_record : v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com; fo=1
```

### References
- RFC 7489 — Section 6.3 (`fo=` tag)

---

## DMARC-016 — DMARC `ri=` Reporting Interval Too High

**Severity:** INFO | **Weight:** 0 | **Automation:** SEMI_AUTOMATIC

### Condition
The DMARC record has an `ri=` value significantly above the default of 86400 (24 hours).

### Detection Logic
DMARC parser reads `ri=` tag. Value exceeds 86400.

### Technical Explanation
RFC 7489 defines `ri=` as the requested interval between aggregate reports in seconds. Default is 86400 (daily). Higher values mean less frequent reports, reducing visibility.

### User Explanation
Your DMARC reports are configured to arrive less frequently than recommended. Daily reports give you better visibility into email security.

### Recommendation
```
action        : Set `ri=86400` for daily aggregate reports (or remove the tag to use default).
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
```

### References
- RFC 7489 — Section 6.3 (`ri=` tag)

---

## DMARC-017 — DMARC Policy Set to Reject (Healthy)

**Severity:** INFO | **Weight:** +10 (BONUS) | **Automation:** N/A | **Positive:** true

### Condition
The DMARC record has `p=reject`.

### Detection Logic
DMARC parser reads `p=` tag. Value is `reject`.

### Business Impact
`p=reject` is the strongest DMARC policy. Unauthorized emails are rejected outright — not delivered and not quarantined. This is the gold standard for email authentication.

### Technical Explanation
RFC 7489: `p=reject` instructs receivers to refuse messages that fail DMARC authentication. It provides the strongest protection against domain spoofing and phishing.

### User Explanation
Excellent — your domain has the strongest possible email security policy. Unauthorized emails claiming to be from your domain are blocked immediately.

### Recommendation
No action required. Maintain `p=reject` and continue monitoring DMARC reports to ensure no legitimate email is failing authentication.

### References
- RFC 7489 — Section 6.3
