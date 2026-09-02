# Recommendation Model

**Document ID:** DKB-007  
**Version:** 1.0  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026

---

## Purpose

This document defines the structure used for all actionable recommendations in the Deliverability Knowledge Base, the priority model for surfacing recommendations to users, and the curated recommendation catalog for the highest-impact insights.

---

## Recommendation Object Schema

Every insight's `recommendation` field follows this structure:

```
action                        : Imperative sentence describing what the user must do.
urgency                       : IMMEDIATE | THIS_WEEK | THIS_MONTH | WHEN_POSSIBLE
effort                        : < 5 MIN | 5–15 MIN | 15–60 MIN | > 1 HOUR
impact                        : HIGH | MEDIUM | LOW — impact on deliverability if resolved
automation_level              : AUTOMATIC | SEMI_AUTOMATIC | MANUAL | NOT_POSSIBLE
prerequisites                 : List of strings (e.g., ["SPF configured", "DKIM configured"])
estimated_deliverability_gain : Integer (e.g., +5, +10)
automation_candidate          : true / false
sample_record                 : Example DNS record value (string, optional)
step_by_step                  : Ordered list of implementation steps (list of strings)
validation_cmd                : DNS query to confirm fix is applied (string, optional)
```

### Field Definitions

**action** — Single imperative sentence. Written for a non-technical marketing user. Must be immediately understandable without technical jargon.  
**urgency** — How quickly the user should act. Driven by severity and business impact.  
**effort** — Realistic time estimate for a non-technical user to complete the fix with guidance.  
**impact** — The deliverability improvement expected if the issue is resolved.  
**automation_level** — Maps to the Automation Engine capabilities.  
**prerequisites** — Technical steps required before this recommendation can be executed.  
**estimated_deliverability_gain** — Point-value estimation of deliverability impact.  
**automation_candidate** — Boolean flag indicating if this can be fully automated using external APIs.  
**sample_record** — A complete, copy-paste-ready DNS record value where applicable.  
**step_by_step** — Numbered instructions a non-technical user can follow.  
**validation_cmd** — A `dig` or `nslookup` command to confirm the fix is live.

---

## Urgency Levels

| Urgency | Definition | Examples |
|---|---|---|
| IMMEDIATE | Fix within hours. Active delivery failure or critical security risk. | No SPF, No DMARC, DKIM revoked, +all |
| THIS_WEEK | Fix within 5 business days. Significant deliverability impact. | DMARC p=none, DKIM 1024-bit |
| THIS_MONTH | Fix within 30 days. Suboptimal configuration. | SPF lookup approaching limit, pct < 100 |
| WHEN_POSSIBLE | Fix at next opportunity. Minor hygiene issue. | Duplicate mechanisms, low TTL |

---

## Effort Levels

| Effort | Definition |
|---|---|
| < 5 MIN | Change one value in a DNS control panel |
| 5–15 MIN | Look up, compose, and publish a DNS record |
| 15–60 MIN | Generate key pairs, configure mail server, or research ESPs |
| > 1 HOUR | Multi-step process requiring tools, external coordination, or provider contact |

---

## Priority Matrix

When multiple recommendations are active, they are surfaced to the user in priority order:

```
Priority = f(urgency, impact, severity)
```

| Priority Rank | Urgency | Impact | Severity |
|---|---|---|---|
| P1 — Critical | IMMEDIATE | HIGH | CRITICAL |
| P2 — High | IMMEDIATE | HIGH or MEDIUM | HIGH |
| P3 — Important | THIS_WEEK | HIGH | HIGH or MEDIUM |
| P4 — Moderate | THIS_WEEK or THIS_MONTH | MEDIUM | MEDIUM |
| P5 — Low | THIS_MONTH or WHEN_POSSIBLE | LOW | LOW |
| P6 — Informational | WHEN_POSSIBLE | LOW | INFO |

**Tiebreaker:** When two recommendations share the same priority rank, the one with the lower effort estimate is surfaced first (quick wins first).

---

## Recommendation Catalog

Top 20 highest-priority insight recommendations with full detail:

---

### REC-000 — Establish Core Email Authentication (XPRO-001)

```yaml
insight_id                    : XPRO-001
action                        : Establish your core email authentication sequence (SPF → DKIM → DMARC).
urgency                       : IMMEDIATE
effort                        : > 1 HOUR
impact                        : HIGH
automation_level              : SEMI_AUTOMATIC
prerequisites                 : []
estimated_deliverability_gain : +50
automation_candidate          : true
step_by_step                  :
  - Sequence begins: First, publish an SPF record authorizing your sending servers.
  - Second, generate and publish a DKIM key pair via your email provider.
  - Wait 24 hours for DNS propagation and test sending to verify signatures.
  - Finally, publish a DMARC record starting with p=none to monitor traffic.
  - Monitor reports for 2-4 weeks before escalating DMARC policy.
```

---

### REC-001 — No SPF Record (SPF-001)

```yaml
insight_id    : SPF-001
action        : Publish a valid SPF TXT record identifying your authorized email sending servers.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
sample_record : v=spf1 include:_spf.google.com ~all
step_by_step  :
  - Identify all services that send email from your domain.
  - Obtain the SPF include: value for each service from their documentation.
  - Build: v=spf1 include:<service1> include:<service2> ~all
  - Log in to your DNS provider.
  - Create a TXT record on your root domain with the constructed value.
  - Save, wait 15 minutes, then validate.
validation_cmd: dig TXT example.com | grep spf
```

---

### REC-002 — No DMARC Record (DMARC-001)

```yaml
insight_id    : DMARC-001
action        : Publish a DMARC TXT record at _dmarc.<yourdomain> to establish your email policy.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
sample_record : v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
step_by_step  :
  - Set up a dedicated email inbox for DMARC reports (e.g., dmarc@yourdomain.com).
  - Log in to your DNS provider.
  - Create a TXT record with hostname: _dmarc
  - Set value to: v=DMARC1; p=none; rua=mailto:<your_report_email>
  - Save and validate.
  - Monitor incoming reports for 2–4 weeks, then escalate policy.
validation_cmd: dig TXT _dmarc.example.com
```

---

### REC-003 — No DKIM Record (DKIM-001)

```yaml
insight_id    : DKIM-001
action        : Generate a DKIM key pair and publish the public key as a TXT record at your selector domain.
urgency       : IMMEDIATE
effort        : 15–60 MIN
impact        : HIGH
sample_record : v=DKIM1; k=rsa; p=<your_base64_public_key>
step_by_step  :
  - Log in to your email service provider (ESP) or mail server admin panel.
  - Locate DKIM settings and generate a new 2048-bit key pair.
  - Copy the provided TXT record value (the public key).
  - In your DNS provider, create a TXT record at <selector>._domainkey.<yourdomain>.
  - Paste the public key value.
  - Save and wait for propagation.
  - Send a test email and check headers for DKIM=pass.
validation_cmd: dig TXT <selector>._domainkey.example.com
```

---

### REC-004 — SPF +all (SPF-005)

```yaml
insight_id    : SPF-005
action        : Replace +all with -all in your SPF record immediately.
urgency       : IMMEDIATE
effort        : < 5 MIN
impact        : HIGH
sample_record : v=spf1 include:_spf.google.com -all
step_by_step  :
  - Log in to your DNS provider.
  - Find the SPF TXT record for your domain.
  - Locate +all or all (without qualifier) at the end.
  - Replace with -all (hard fail) or ~all (soft fail) if testing.
  - Save and verify.
validation_cmd: dig TXT example.com | grep spf
```

---

### REC-005 — Multiple SPF Records (SPF-002)

```yaml
insight_id    : SPF-002
action        : Merge all SPF records into one and delete the extras.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
step_by_step  :
  - Query all TXT records to find every v=spf1 record.
  - Combine all include: and ip4: mechanisms from all records into one single record.
  - Ensure one all mechanism at end (preferably ~all or -all).
  - Delete all extra SPF TXT records from your DNS.
  - Publish only the merged single record.
  - Verify only one SPF record remains.
validation_cmd: dig TXT example.com | grep spf
```

---

### REC-006 — DKIM Key Too Short (DKIM-006)

```yaml
insight_id    : DKIM-006
action        : Generate a new 2048-bit DKIM key pair to replace the insecure short key.
urgency       : IMMEDIATE
effort        : 15–60 MIN
impact        : HIGH
step_by_step  :
  - Generate a new 2048-bit RSA key pair in your ESP or using openssl.
  - Publish the new public key at a new selector (e.g., selector2._domainkey.<domain>).
  - Configure your mail server to sign using the new private key and new selector.
  - Verify DKIM pass in test email headers.
  - After confirming, deprecate (or delete) the old short-key selector record.
```

---

### REC-007 — SPF Lookup Limit Exceeded (SPF-008)

```yaml
insight_id    : SPF-008
action        : Reduce SPF DNS lookup count below 10 by consolidating or removing includes.
urgency       : IMMEDIATE
effort        : 15–60 MIN
impact        : HIGH
step_by_step  :
  - Use MXToolbox or a similar tool to count your current SPF lookup depth.
  - Identify include: domains for services you no longer use — remove them.
  - For remaining includes, check if the ESP offers direct ip4: CIDR ranges instead.
  - Replace includes with ip4: where possible (SPF flattening).
  - Republish the optimized record and verify lookup count.
  - Target ≤ 6 lookups for safe headroom.
validation_cmd: dig TXT example.com | grep spf
```

---

### REC-008 — DMARC p=none (DMARC-005)

```yaml
insight_id    : DMARC-005
action        : Review DMARC reports and escalate your policy from p=none to p=quarantine.
urgency       : THIS_MONTH
effort        : < 5 MIN
impact        : HIGH
sample_record : v=DMARC1; p=quarantine; pct=25; rua=mailto:dmarc@yourdomain.com
step_by_step  :
  - Review aggregate DMARC reports for 2–4 weeks.
  - Confirm all legitimate email sources pass SPF and DKIM.
  - Change p=none to p=quarantine with pct=25 initially.
  - Monitor for 2 weeks. If no legitimate failures, increase pct to 100.
  - After full quarantine, plan the move to p=reject.
validation_cmd: dig TXT _dmarc.example.com
```

---

### REC-009 — Missing PTR Record (DNS-004)

```yaml
insight_id    : DNS-004
action        : Contact your hosting or IP provider to create a PTR (reverse DNS) record for your mail server IP.
urgency       : THIS_WEEK
effort        : > 1 HOUR
impact        : HIGH
step_by_step  :
  - Identify your outbound mail server's public IP address.
  - Contact your hosting provider or ISP (this cannot be done in your own DNS panel).
  - Request they create a PTR record: <your_IP> resolves to <your_mail_hostname>.
  - Ask the hosting provider to also verify forward-confirmed reverse DNS (FCrDNS).
  - Validate with: dig -x <your_mail_IP>
validation_cmd: dig -x <your_mail_server_IP>
```

---

### REC-010 — DMARC Missing rua= (DMARC-006)

```yaml
insight_id    : DMARC-006
action        : Add an rua= reporting address to your DMARC record to start receiving authentication reports.
urgency       : THIS_WEEK
effort        : < 5 MIN
impact        : HIGH
sample_record : v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
step_by_step  :
  - Create a dedicated inbox for DMARC reports (e.g., dmarc@yourdomain.com) or sign up for a DMARC reporting service.
  - Edit your DMARC record to add: rua=mailto:<your_address>
  - Save and verify.
  - Confirm reports arrive within 24 hours.
validation_cmd: dig TXT _dmarc.example.com
```

---

### REC-011 — DKIM Key Revoked (DKIM-004)

```yaml
insight_id    : DKIM-004
action        : Generate and publish a new DKIM public key to replace the revoked one.
urgency       : IMMEDIATE
effort        : 15–60 MIN
impact        : HIGH
step_by_step  :
  - Generate a new 2048-bit RSA DKIM key pair.
  - Publish the new public key at your selector domain (or a new selector name).
  - Update your mail server configuration with the new private key and selector.
  - Send a test email and verify DKIM=pass.
```

---

### REC-012 — No MX Record (DNS-001)

```yaml
insight_id    : DNS-001
action        : Publish an MX record pointing to your mail server hostname.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
sample_record : example.com. IN MX 10 mail.example.com.
step_by_step  :
  - Log in to your DNS provider.
  - Create a new MX record for your root domain.
  - Set priority to 10.
  - Set value to your mail server hostname (e.g., mail.example.com or your ESP's hostname).
  - Save, wait for propagation, and verify.
validation_cmd: dig MX example.com
```

---

### REC-013 — DKIM 1024-bit Key (DKIM-007)

```yaml
insight_id    : DKIM-007
action        : Upgrade your DKIM key from 1024 to 2048 bits using a new selector.
urgency       : THIS_MONTH
effort        : 15–60 MIN
impact        : MEDIUM
step_by_step  :
  - Generate a new 2048-bit DKIM key pair.
  - Publish the new public key at a new selector (e.g., selector2024._domainkey.<domain>).
  - Update your mail server to sign with the new key and selector.
  - Verify DKIM pass in test email headers.
  - After confirming the new key works, delete the old 1024-bit selector record.
```

---

### REC-014 — DMARC pct < 100 (DMARC-011)

```yaml
insight_id    : DMARC-011
action        : Increase your DMARC pct= value to 100% to apply your policy to all email.
urgency       : THIS_MONTH
effort        : < 5 MIN
impact        : MEDIUM
step_by_step  :
  - Review DMARC reports to confirm all legitimate mail is passing.
  - Edit the DMARC record and change pct=<current> to pct=100.
  - Save and monitor for failures.
```

---

### REC-015 — SPF Lookup Approaching Limit (SPF-013)

```yaml
insight_id    : SPF-013
action        : Proactively reduce SPF lookup count to create headroom before the 10-lookup limit is reached.
urgency       : THIS_WEEK
effort        : 15–60 MIN
impact        : MEDIUM
step_by_step  :
  - Audit current include: domains and identify unused services.
  - Remove unused includes from the SPF record.
  - Consider replacing remaining includes with direct ip4: ranges.
  - Target ≤ 6 lookups.
```

---

### REC-016 — DMARC Alignment Failure (XPRO-003)

```yaml
insight_id    : XPRO-003
action        : Align your email sending configuration so the signing domain matches your From: address domain.
urgency       : THIS_WEEK
effort        : 15–60 MIN
impact        : HIGH
step_by_step  :
  - Check the DKIM d= value in outbound email headers (view raw email source).
  - If d= is your ESP's domain (not yours), configure your ESP to sign with your domain.
  - Check the Return-Path domain (envelope-from) matches your From: domain for SPF alignment.
  - If using relaxed alignment, ensure the d= is at minimum a parent domain of From:.
  - Test with a DMARC alignment checker tool.
```

---

### REC-017 — DKIM Testing Mode (DKIM-015)

```yaml
insight_id    : DKIM-015
action        : Remove the t=y testing mode flag from your DKIM record.
urgency       : THIS_WEEK
effort        : < 5 MIN
impact        : MEDIUM
step_by_step  :
  - Log in to your DNS provider.
  - Locate the DKIM TXT record at <selector>._domainkey.<domain>.
  - Remove the t=y tag from the record value.
  - Save and verify.
```

---

### REC-018 — CNAME at Root Domain (DNS-006)

```yaml
insight_id    : DNS-006
action        : Replace the CNAME record at your root domain with an A record.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
sample_record : example.com. IN A 203.0.113.1
step_by_step  :
  - Log in to your DNS provider.
  - Delete the CNAME record at the root domain level (@ or blank hostname).
  - Create an A record pointing to your web server or mail server IP.
  - If using a CDN, check if your provider supports ALIAS or CNAME flattening.
  - Save and verify.
```

---

### REC-019 — SPF Missing `all` (SPF-006)

```yaml
insight_id    : SPF-006
action        : Add ~all to the end of your SPF record to define behavior for unauthorized senders.
urgency       : THIS_WEEK
effort        : < 5 MIN
impact        : HIGH
sample_record : v=spf1 include:_spf.google.com ~all
step_by_step  :
  - Locate your SPF TXT record.
  - Add ~all at the end of the record value.
  - Save and verify.
```

---

### REC-020 — DMARC Subdomain Not Protected (DMARC-012)

```yaml
insight_id    : DMARC-012
action        : Add sp=reject to your DMARC record to protect your subdomains from spoofing.
urgency       : THIS_WEEK
effort        : < 5 MIN
impact        : MEDIUM
sample_record : v=DMARC1; p=quarantine; sp=reject; rua=mailto:dmarc@yourdomain.com
step_by_step  :
  - Edit your DMARC record.
  - Add sp=reject (or sp=quarantine to match your root policy level).
  - Save and verify.
validation_cmd: dig TXT _dmarc.example.com
```
