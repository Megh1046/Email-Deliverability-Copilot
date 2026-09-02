# DNS Insights

**Document ID:** DKB-001  
**Version:** 1.0  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026  
**Protocol:** DNS  
**Total Insights:** 12

---

## Summary Table

| ID | Title | Severity | Automation |
|---|---|---|---|
| DNS-001 | No MX Record Found | CRITICAL | SEMI_AUTOMATIC |
| DNS-002 | MX Record Points to IP Address | HIGH | SEMI_AUTOMATIC |
| DNS-003 | Multiple Conflicting MX Records | HIGH | MANUAL |
| DNS-004 | Missing PTR / Reverse DNS Record | HIGH | NOT_POSSIBLE |
| DNS-005 | Missing A Record for Root Domain | MEDIUM | SEMI_AUTOMATIC |
| DNS-006 | CNAME at Root Domain | HIGH | SEMI_AUTOMATIC |
| DNS-007 | No NS Records Resolvable | CRITICAL | NOT_POSSIBLE |
| DNS-008 | Domain NX — Non-Existent Domain | CRITICAL | NOT_POSSIBLE |
| DNS-009 | Low TTL on MX Records | LOW | SEMI_AUTOMATIC |
| DNS-010 | MX Record Priority Misconfiguration | LOW | SEMI_AUTOMATIC |
| DNS-011 | SOA Record Missing or Malformed | MEDIUM | NOT_POSSIBLE |
| DNS-012 | Excessive DNS Propagation Delay | MEDIUM | NOT_POSSIBLE |

---

## DNS-001 — No MX Record Found

**Title:** No MX Record Found  
**Category:** DNS  
**Protocol:** DNS  
**Severity:** CRITICAL  
**Positive:** false  
**Confidence Weight:** -25

### Condition
No MX record exists for the queried domain.

### Detection Logic
DNS resolver returns an empty answer set for the MX query type on the root domain.

### Business Impact
Sending servers cannot determine where to deliver email for this domain. All inbound email will fail. Outbound deliverability is also impacted because receiving servers viewing the domain as mail-capable will find it missing essential infrastructure.

### Technical Explanation
MX (Mail Exchanger) records designate the mail servers responsible for accepting email for a domain. Without an MX record, remote SMTP servers performing RFC 5321 mail routing will either attempt delivery to the A record (fallback behavior, not RFC-recommended) or reject the message. Most enterprise providers reject.

### User Explanation
Your domain has no mail server configured. Email sent to your domain will not be delivered, and your sender reputation may be impacted because providers cannot verify your mail infrastructure.

### Recommendation
```
action        : Publish a valid MX record pointing to your mail server hostname.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
sample_record : example.com. IN MX 10 mail.example.com.
step_by_step  :
  1. Log in to your DNS provider.
  2. Create a new MX record for your root domain.
  3. Set priority to 10 (or your mail provider's recommended value).
  4. Set the value to your mail server hostname (e.g., mail.example.com).
  5. Save and wait for DNS propagation (typically 15–60 minutes).
validation_cmd: dig MX example.com
```

### Automation Level
SEMI_AUTOMATIC — The system can generate the exact MX record. The user must publish it via their DNS provider.

### Dependencies
None

### References
- RFC 5321 — SMTP Mail Routing  
- RFC 1035 — MX Record Specification  

---

## DNS-002 — MX Record Points to IP Address

**Title:** MX Record Points to IP Address (Not Hostname)  
**Category:** DNS  
**Protocol:** DNS  
**Severity:** HIGH  
**Positive:** false  
**Confidence Weight:** -15

### Condition
An MX record value is an IP address (IPv4 or IPv6) instead of a fully qualified domain name (FQDN).

### Detection Logic
DNS resolver returns MX record. The value of the MX record matches the regex pattern for an IPv4 or IPv6 address rather than a domain name.

### Business Impact
This is an RFC violation. Some mail servers will refuse to deliver email to IP-based MX records, causing delivery failures with major providers.

### Technical Explanation
RFC 2181 Section 10.3 and RFC 5321 Section 5 specify that MX record values MUST be hostnames, not IP addresses. An MX value of `10 203.0.113.5` is technically invalid. Compliant SMTP servers will reject this configuration.

### User Explanation
Your mail server address is incorrectly set. Instead of using a name like `mail.example.com`, it's using a raw IP address. This can cause email delivery to fail with major email providers.

### Recommendation
```
action        : Replace the IP address in your MX record with a valid hostname.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
sample_record : example.com. IN MX 10 mail.example.com.
step_by_step  :
  1. Create an A record for your mail server hostname (e.g., mail.example.com → your IP).
  2. Update the MX record to use the hostname instead of the raw IP.
  3. Save and verify propagation.
validation_cmd: dig MX example.com
```

### Automation Level
SEMI_AUTOMATIC — System can generate the corrected MX and A records.

### Dependencies
None

### References
- RFC 2181 — Section 10.3  
- RFC 5321 — Section 5  

---

## DNS-003 — Multiple Conflicting MX Records

**Title:** Multiple Conflicting MX Records  
**Category:** DNS  
**Protocol:** DNS  
**Severity:** HIGH  
**Positive:** false  
**Confidence Weight:** -15

### Condition
Multiple MX records exist but point to hosts that appear to belong to different, conflicting mail providers (e.g., Google Workspace + Microsoft 365 simultaneously).

### Detection Logic
DNS resolver returns two or more MX records. The hostnames belong to distinct provider namespaces (e.g., `*.google.com` and `*.protection.outlook.com`).

### Business Impact
Inbound email may be split between providers, resulting in lost messages and inconsistent delivery. Both providers will also consider configuration invalid.

### Technical Explanation
While multiple MX records are valid for failover purposes, having records pointing to separate email hosting providers creates an ambiguous configuration. Sending servers will attempt delivery to one provider, but inbox access may be on the other. Messages will be silently dropped.

### User Explanation
Your domain is configured to send email to two different email services at the same time (e.g., both Google and Microsoft). This causes email to get lost. You need to choose one provider.

### Recommendation
```
action        : Remove MX records for all except your active email provider.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
step_by_step  :
  1. Confirm which email provider is your active provider.
  2. Delete all MX records belonging to the inactive provider.
  3. Confirm the remaining MX records belong to the active provider only.
validation_cmd: dig MX example.com
```

### Automation Level
MANUAL — Requires user to identify the correct provider before records can be cleaned.

### Dependencies
None

### References
- RFC 5321 — Section 5.1  

---

## DNS-004 — Missing PTR / Reverse DNS Record

**Title:** Missing PTR / Reverse DNS Record  
**Category:** DNS Health  
**Protocol:** DNS  
**Severity:** HIGH  
**Positive:** false  
**Confidence Weight:** -15

### Condition
No PTR record exists for the IP address of the outbound mail server.

### Detection Logic
Reverse DNS query (`in-addr.arpa`) on the sending server's IP address returns NXDOMAIN or no answer.

### Business Impact
Major inbox providers (Gmail, Outlook, Yahoo) check for a valid reverse DNS record before accepting email. Missing PTR records are a significant spam signal. Delivery rates drop materially.

### Technical Explanation
A PTR record maps an IP address to a hostname. For mail delivery, the hostname returned by the PTR record should match the hostname used in the SMTP EHLO/HELO greeting and the HELO hostname should resolve back to the IP (forward-confirmed reverse DNS, or FCrDNS). Absence of PTR is one of the top spam signals used by ISP filters.

### User Explanation
Your outbound mail server doesn't have a "reverse address" — a record that lets receiving servers confirm your server is legitimate. Major email services like Gmail and Outlook use this to detect spam. Without it, your emails are more likely to be blocked.

### Recommendation
```
action        : Request a PTR record from your hosting or IP address provider.
urgency       : THIS_WEEK
effort        : 15–60 MIN
impact        : HIGH
step_by_step  :
  1. Identify your outbound mail server IP address.
  2. Contact your hosting provider or ISP (PTR records can only be set by the IP owner).
  3. Request they create a PTR record: <your_IP> → <your_mail_hostname>.
  4. Verify the forward and reverse DNS match (FCrDNS).
validation_cmd: dig -x <your_mail_server_IP>
```

### Automation Level
NOT_POSSIBLE — PTR records are controlled by the IP address owner (hosting provider), not the domain owner.

### Dependencies
None

### References
- RFC 1912 — Common DNS Operational and Configuration Errors  
- RFC 5321 — Section 2.3.5  

---

## DNS-005 — Missing A Record for Root Domain

**Title:** Missing A Record for Root Domain  
**Category:** DNS  
**Protocol:** DNS  
**Severity:** MEDIUM  
**Positive:** false  
**Confidence Weight:** -8

### Condition
No A record (IPv4) exists for the apex / root domain.

### Detection Logic
DNS resolver returns empty answer for A record query on the root domain (e.g., `example.com`).

### Business Impact
Some mail servers perform a fallback A record lookup when MX is missing. Additionally, the absence of an A record can signal a domain that is not fully operational, which some spam filters flag as suspicious.

### Technical Explanation
While not strictly required for email delivery when MX records are correctly set, a missing root A record is a hygiene problem. RFC 5321 Section 5.1 allows A-record fallback for mail routing when MX is absent. It also affects web presence and domain credibility checks used by reputation systems.

### User Explanation
Your domain doesn't have a basic address record. This doesn't directly break email but makes your domain look incomplete to some email providers, potentially affecting your sender reputation.

### Recommendation
```
action        : Add an A record for your root domain.
urgency       : THIS_WEEK
effort        : < 5 MIN
impact        : MEDIUM
sample_record : example.com. IN A 203.0.113.1
step_by_step  :
  1. Log in to your DNS provider.
  2. Create an A record for @ (root domain) pointing to your web server or mail server IP.
  3. Save and verify propagation.
validation_cmd: dig A example.com
```

### Automation Level
SEMI_AUTOMATIC — Record can be generated; user must apply.

### Dependencies
None

### References
- RFC 5321 — Section 5.1  

---

## DNS-006 — CNAME at Root Domain

**Title:** CNAME at Root Domain (RFC Violation)  
**Category:** DNS  
**Protocol:** DNS  
**Severity:** HIGH  
**Positive:** false  
**Confidence Weight:** -15

### Condition
A CNAME record exists at the apex / root domain level instead of an A record.

### Detection Logic
DNS resolver returns a CNAME record for the root domain (e.g., `example.com CNAME otherwebsite.com`).

### Business Impact
RFC 1034 explicitly prohibits CNAME records at the apex domain. This breaks MX, NS, SOA, and SPF record resolution because CNAME records cannot coexist with other record types. Email delivery from this domain is likely broken.

### Technical Explanation
Per RFC 1034 Section 3.6.2, a CNAME record at the root domain is invalid because the root must host NS and SOA records. If a CNAME is placed there, DNS resolvers must stop resolution when they find it, meaning MX lookups and TXT (SPF) lookups will fail. Some providers use CNAME flattening as a workaround, but this is non-standard and not universally supported.

### User Explanation
Your domain's main address record is set up incorrectly. This type of error can break all email delivery from your domain. It needs to be corrected at your DNS provider.

### Recommendation
```
action        : Replace the root CNAME with an A record.
urgency       : IMMEDIATE
effort        : 5–15 MIN
impact        : HIGH
sample_record : example.com. IN A 203.0.113.1
step_by_step  :
  1. Delete the CNAME record at the root domain.
  2. Add an A record (IPv4) or AAAA record (IPv6) pointing to your server.
  3. If using a CDN, check if your provider supports CNAME flattening or ALIAS records.
validation_cmd: dig A example.com
```

### Automation Level
SEMI_AUTOMATIC — System can generate the correct A record; user must apply.

### Dependencies
None

### References
- RFC 1034 — Section 3.6.2  

---

## DNS-007 — No NS Records Resolvable

**Title:** No NS Records Resolvable  
**Category:** DNS Health  
**Protocol:** DNS  
**Severity:** CRITICAL  
**Positive:** false  
**Confidence Weight:** -25

### Condition
DNS queries for the domain's NS records return no results or a SERVFAIL response.

### Detection Logic
DNS resolver returns SERVFAIL or empty ANSWER for NS record query on the root domain.

### Business Impact
If name servers are not responding, all DNS resolution for the domain fails. Email delivery, website access, and all DNS-dependent services are completely broken.

### Technical Explanation
NS records identify the authoritative name servers for a domain. If those servers are unreachable or return SERVFAIL, the domain is effectively offline from a DNS perspective. This is a hosting or domain registrar level issue.

### User Explanation
Your domain's name servers are not responding. This is the most severe possible DNS problem — it means nothing about your domain can be looked up, and all email delivery has stopped.

### Recommendation
```
action        : Contact your domain registrar or DNS hosting provider immediately.
urgency       : IMMEDIATE
effort        : > 1 HOUR
impact        : HIGH
step_by_step  :
  1. Check if your domain registration is active (not expired).
  2. Verify your registrar has the correct NS records pointed to your DNS host.
  3. Contact your DNS hosting provider if name servers are down.
  4. If recently migrated DNS, allow up to 48 hours for full propagation.
validation_cmd: dig NS example.com
```

### Automation Level
NOT_POSSIBLE — NS record issues require action at the registrar or DNS host level.

### Dependencies
None

### References
- RFC 1034 — Name Server Concepts  
- RFC 1035 — Domain Implementation and Specification  

---

## DNS-008 — Domain NX — Non-Existent Domain

**Title:** Domain NX — Non-Existent Domain  
**Category:** DNS Health  
**Protocol:** DNS  
**Severity:** CRITICAL  
**Positive:** false  
**Confidence Weight:** -25

### Condition
DNS resolver returns NXDOMAIN for the queried domain.

### Detection Logic
Any DNS query for the root domain returns NXDOMAIN (DNS response code 3).

### Business Impact
The domain does not exist in DNS. No email can be sent to or from this domain. Analysis cannot proceed until the domain is registered and DNS is active.

### Technical Explanation
NXDOMAIN indicates the queried domain name does not exist in the DNS namespace. This is typically caused by an unregistered domain, an expired domain registration, or a domain that has been deleted.

### User Explanation
This domain doesn't exist in the global internet directory (DNS). Email sent from or to this domain will fail immediately. The domain needs to be registered or its registration needs to be renewed.

### Recommendation
```
action        : Register the domain or renew the expired registration.
urgency       : IMMEDIATE
effort        : > 1 HOUR
impact        : HIGH
step_by_step  :
  1. Verify if the domain is registered using a WHOIS lookup.
  2. If expired, renew with your domain registrar immediately.
  3. If intentionally new, register the domain and configure DNS.
  4. Wait for global DNS propagation (up to 48 hours).
```

### Automation Level
NOT_POSSIBLE — Domain registration is outside DNS control.

### Dependencies
None

### References
- RFC 1035 — NXDOMAIN response code  

---

## DNS-009 — Low TTL on MX Records

**Title:** Low TTL on MX Records  
**Category:** DNS  
**Protocol:** DNS  
**Severity:** LOW  
**Positive:** false  
**Confidence Weight:** -3

### Condition
MX records have a TTL lower than 300 seconds (5 minutes).

### Detection Logic
DNS resolver returns MX records with TTL value < 300.

### Business Impact
Extremely low TTLs cause receiving mail servers to perform excessive DNS lookups for every delivery attempt. This can contribute to temporary delivery delays during high-volume sending and increases DNS query load.

### Technical Explanation
A low TTL means the record expires from DNS cache very quickly, causing resolvers to query authoritative DNS servers more frequently. During mail queue retries, very low TTL is not typically harmful but is considered poor hygiene for stable production infrastructure.

### User Explanation
Your mail server address is set to refresh very frequently. While not immediately harmful, it creates unnecessary overhead and is not standard practice for a stable mail configuration.

### Recommendation
```
action        : Increase the MX record TTL to at least 3600 seconds (1 hour).
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
impact        : LOW
sample_record : example.com. 3600 IN MX 10 mail.example.com.
step_by_step  :
  1. Log in to your DNS provider.
  2. Find the MX record(s) for your domain.
  3. Change the TTL value to 3600 (or your provider's recommended value).
  4. Save changes.
validation_cmd: dig MX example.com
```

### Automation Level
SEMI_AUTOMATIC — Record update can be generated; user must apply.

### Dependencies
None

### References
- RFC 1035 — TTL field specification  

---

## DNS-010 — MX Record Priority Misconfiguration

**Title:** MX Record Priority Misconfiguration  
**Category:** DNS  
**Protocol:** DNS  
**Severity:** LOW  
**Positive:** false  
**Confidence Weight:** -3

### Condition
All MX records have an identical priority value when multiple records exist, or a primary MX has a higher priority number than the backup (reversed priority).

### Detection Logic
DNS resolver returns multiple MX records. Either all priorities are equal, or the primary server has a numerically higher priority than a secondary (which makes it lower priority in MX routing logic).

### Business Impact
If priorities are equal, delivery load is randomly distributed across all servers. If priorities are reversed, backup servers will receive email before the primary, potentially causing messages to bypass intended routing.

### Technical Explanation
In MX routing, a lower numerical priority value means higher precedence. A primary server should have a lower number (e.g., 10) than its backup (e.g., 20). Equal priority values cause round-robin delivery, which may not be intended.

### User Explanation
Your mail server priority settings are configured incorrectly. This can cause email to be delivered to a backup server instead of your main inbox, or split randomly between servers.

### Recommendation
```
action        : Set primary MX to a lower priority number than backup servers.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
impact        : LOW
sample_record : Primary: example.com. IN MX 10 mail.example.com. | Backup: example.com. IN MX 20 backup.example.com.
step_by_step  :
  1. Identify your primary and backup mail servers.
  2. Set the primary server MX priority to 10.
  3. Set backup servers to 20 or higher.
  4. Save and verify.
validation_cmd: dig MX example.com
```

### Automation Level
SEMI_AUTOMATIC — Correct records can be generated; user must apply.

### Dependencies
DNS-001

### References
- RFC 5321 — Section 5.1 — MX Record Priority  

---

## DNS-011 — SOA Record Missing or Malformed

**Title:** SOA Record Missing or Malformed  
**Category:** DNS Health  
**Protocol:** DNS  
**Severity:** MEDIUM  
**Positive:** false  
**Confidence Weight:** -8

### Condition
The SOA (Start of Authority) record is absent or contains syntactically invalid field values.

### Detection Logic
DNS resolver returns no SOA record, or the SOA record fails to parse expected fields (MNAME, RNAME, SERIAL, REFRESH, RETRY, EXPIRE, MINIMUM TTL).

### Business Impact
A missing or malformed SOA record indicates DNS zone misconfiguration. This can cause zone transfer failures, secondary DNS server issues, and negative caching problems that delay recovery from DNS errors.

### Technical Explanation
The SOA record is mandatory for every DNS zone. It contains the primary NS name, administrator email, zone serial number, and timing parameters (refresh, retry, expire, minimum TTL). Absence indicates a broken DNS zone configuration.

### User Explanation
Your domain's DNS zone configuration is incomplete or broken at a fundamental level. This isn't immediately visible to email senders, but it can cause delayed recovery when DNS records are changed and may indicate other DNS problems.

### Recommendation
```
action        : Contact your DNS hosting provider to verify SOA record is correctly published.
urgency       : THIS_WEEK
effort        : 15–60 MIN
impact        : MEDIUM
step_by_step  :
  1. Query your SOA record to confirm the issue.
  2. Log in to your DNS provider's control panel.
  3. Re-create the DNS zone if the SOA is absent.
  4. Verify with your DNS provider that zone configuration is correct.
validation_cmd: dig SOA example.com
```

### Automation Level
NOT_POSSIBLE — SOA records are managed by the DNS hosting provider.

### Dependencies
None

### References
- RFC 1035 — SOA Record  
- RFC 1912 — Common DNS Operational Errors  

---

## DNS-012 — Excessive DNS Propagation Delay

**Title:** Excessive DNS Propagation Delay  
**Category:** DNS Health  
**Protocol:** DNS  
**Severity:** MEDIUM  
**Positive:** false  
**Confidence Weight:** -8

### Condition
DNS records recently changed are not yet visible from multiple global DNS resolvers after the expected propagation window.

### Detection Logic
Querying multiple geographically distributed resolvers (e.g., 8.8.8.8, 1.1.1.1, 9.9.9.9) returns inconsistent results for the same record type within the same domain.

### Business Impact
During propagation, some mail servers see old records while others see updated records. This creates intermittent delivery failures and alignment issues (especially for SPF and DMARC) during the transition window.

### Technical Explanation
DNS propagation is not instantaneous; changes must replicate across all authoritative name servers and TTL-governed caches globally. Inconsistent results across resolvers during this window is normal but can impact deliverability if the old records conflict with the new.

### User Explanation
Your recent DNS changes haven't fully spread across the internet yet. During this period, some email providers may see your old settings while others see the new ones. This can cause temporary delivery problems.

### Recommendation
```
action        : Wait for full DNS propagation. Monitor resolver consistency before sending high-volume email.
urgency       : THIS_WEEK
effort        : < 5 MIN
impact        : MEDIUM
step_by_step  :
  1. Use a DNS propagation checker to monitor spread globally.
  2. Wait until all resolvers return consistent results.
  3. Verify your new records are visible from at least 5 different resolver locations.
  4. Send test emails after full propagation is confirmed.
```

### Automation Level
NOT_POSSIBLE — Propagation is a time-based DNS process.

### Dependencies
None

### References
- RFC 1035 — TTL and caching  
