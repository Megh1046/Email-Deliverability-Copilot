# SPF Insights

**Document ID:** DKB-002  
**Version:** 1.0  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026  
**Protocol:** SPF  
**Total Insights:** 17

---

## Summary Table

| ID | Title | Severity | Automation |
|---|---|---|---|
| SPF-001 | No SPF Record Found | CRITICAL | SEMI_AUTOMATIC |
| SPF-002 | Multiple SPF Records | CRITICAL | SEMI_AUTOMATIC |
| SPF-003 | SPF Version Missing or Incorrect | CRITICAL | SEMI_AUTOMATIC |
| SPF-004 | SPF Record Contains Syntax Error | CRITICAL | SEMI_AUTOMATIC |
| SPF-005 | SPF Record Ends with `+all` (Permissive) | CRITICAL | SEMI_AUTOMATIC |
| SPF-006 | SPF Record Has No `all` Mechanism | HIGH | SEMI_AUTOMATIC |
| SPF-007 | SPF Record Ends with `?all` (Neutral) | HIGH | SEMI_AUTOMATIC |
| SPF-008 | SPF DNS Lookup Limit Exceeded (> 10) | HIGH | SEMI_AUTOMATIC |
| SPF-009 | `include:` Domain Does Not Exist | HIGH | MANUAL |
| SPF-010 | `include:` Domain Has No SPF Record | HIGH | MANUAL |
| SPF-011 | SPF Record Too Long | MEDIUM | SEMI_AUTOMATIC |
| SPF-012 | SPF Uses Deprecated `ptr` Mechanism | MEDIUM | SEMI_AUTOMATIC |
| SPF-013 | SPF Lookup Approaching Limit (8–10) | MEDIUM | SEMI_AUTOMATIC |
| SPF-014 | `redirect=` and `all` Used Together | HIGH | SEMI_AUTOMATIC |
| SPF-015 | Duplicate Mechanisms in SPF Record | LOW | SEMI_AUTOMATIC |
| SPF-016 | SPF Has Redundant `ip4` Ranges | LOW | SEMI_AUTOMATIC |
| SPF-017 | SPF Record Uses Unknown Modifier | INFO | MANUAL |

---

## SPF-001 — No SPF Record Found

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
No TXT record matching `v=spf1` exists for the domain.

### Detection Logic
DNS resolver returns no TXT records matching the pattern `v=spf1`.

### Business Impact
Without SPF, receiving servers cannot verify which servers are authorized to send email from your domain. Messages are likely spam-filtered or rejected.

### Technical Explanation
SPF (RFC 7208) requires a `v=spf1` TXT record at the root domain. Absence means any server can claim to send email from your domain without challenge — making the domain trivially spoofable.

### User Explanation
Your domain has no email sender authorization record. Email providers can't verify your emails are legitimate and are likely to mark them as spam or reject them.

### Recommendation
```
action        : Publish a valid SPF TXT record identifying authorized sending servers.
urgency       : IMMEDIATE
effort        : 5–15 MIN
sample_record : v=spf1 include:_spf.google.com ~all
step_by_step  :
  1. Identify all services that send email from your domain.
  2. Obtain SPF include values from each service.
  3. Construct an SPF record combining all includes with ~all ending.
  4. Publish as a TXT record on your root domain.
validation_cmd: dig TXT example.com | grep spf
```

### References
- RFC 7208 — Sender Policy Framework

---

## SPF-002 — Multiple SPF Records

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
Two or more TXT records beginning with `v=spf1` exist on the same domain.

### Detection Logic
DNS resolver returns multiple TXT records matching `v=spf1`.

### Business Impact
RFC 7208 §3.2 mandates `permerror` when multiple SPF records exist. Most receiving servers treat this as SPF failure.

### Technical Explanation
This typically happens when a second ESP is added and a new SPF record is published without merging it into the existing one.

### User Explanation
You have two separate SPF records where only one is allowed. Email providers return an error and may reject your messages.

### Recommendation
```
action        : Merge all SPF content into a single TXT record and delete the extras.
urgency       : IMMEDIATE
effort        : 5–15 MIN
sample_record : v=spf1 include:_spf.google.com include:sendgrid.net ~all
step_by_step  :
  1. Retrieve all SPF TXT records for your domain.
  2. Merge all mechanisms into one record.
  3. Delete all extra SPF TXT records.
  4. Publish the single merged record.
validation_cmd: dig TXT example.com | grep spf
```

### References
- RFC 7208 — Section 3.2

---

## SPF-003 — SPF Version Missing or Incorrect

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
A TXT record exists resembling SPF but does not begin with exactly `v=spf1`.

### Detection Logic
TXT records present but none begin with the exact string `v=spf1`.

### Business Impact
The record will not be recognized as SPF. Domain is treated as having no SPF record.

### Technical Explanation
RFC 7208 §4.5 requires `v=spf1` as the first token exactly. Any variation causes silent ignoring.

### User Explanation
Your email authorization record has a formatting error that makes it invisible to email providers.

### Recommendation
```
action        : Correct the SPF record to start with exactly `v=spf1`.
urgency       : IMMEDIATE
effort        : < 5 MIN
sample_record : v=spf1 include:_spf.google.com ~all
validation_cmd: dig TXT example.com | grep spf
```

### References
- RFC 7208 — Section 4.5

---

## SPF-004 — SPF Record Contains Syntax Error

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
SPF record exists but contains invalid mechanisms, modifiers, or formatting errors.

### Detection Logic
SPF parser fails to parse one or more tokens in the record.

### Business Impact
Returns `permerror`. Receiving servers treat this as SPF failure.

### Technical Explanation
RFC 7208 defines strict grammar. Invalid tokens include unknown mechanisms, invalid qualifiers, missing `:` after `include`, and malformed CIDR notation.

### User Explanation
Your authorization record has a typo or formatting error that makes it unreadable by email providers.

### Recommendation
```
action        : Review and correct SPF syntax using a validator tool.
urgency       : IMMEDIATE
effort        : 5–15 MIN
step_by_step  :
  1. Retrieve the current SPF record.
  2. Use an SPF syntax validator to identify the error.
  3. Correct and republish.
validation_cmd: dig TXT example.com | grep spf
```

### References
- RFC 7208 — Sections 5 and 7

---

## SPF-005 — SPF Ends with `+all` (Permissive Allow-All)

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
The SPF record's final mechanism is `+all` or `all` (implicit `+`).

### Business Impact
`+all` grants SPF PASS to every server on the internet. SPF is completely nullified as an anti-spoofing tool.

### Technical Explanation
The `all` mechanism with `+` qualifer passes any IP not matched by prior mechanisms. This is equivalent to no SPF from a security perspective.

### User Explanation
Your domain authorizes every server in the world to send email on your behalf. This is a critical security risk.

### Recommendation
```
action        : Replace `+all` with `~all` or `-all` immediately.
urgency       : IMMEDIATE
effort        : < 5 MIN
sample_record : v=spf1 include:_spf.google.com -all
validation_cmd: dig TXT example.com | grep spf
```

### References
- RFC 7208 — Section 5.1

---

## SPF-006 — SPF Has No `all` Mechanism

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
Valid SPF record exists but has no `all` mechanism at the end.

### Technical Explanation
RFC 7208 §4.7: if no mechanism matches and no `redirect` modifier exists, result is neutral. Non-matching IPs get neutral result instead of fail.

### User Explanation
Your record doesn't tell email providers what to do with unauthorized senders. They get a "no comment" rather than being flagged.

### Recommendation
```
action        : Add `~all` to the end of your SPF record.
urgency       : THIS_WEEK
effort        : < 5 MIN
sample_record : v=spf1 include:_spf.google.com ~all
validation_cmd: dig TXT example.com | grep spf
```

### References
- RFC 7208 — Section 4.7

---

## SPF-007 — SPF Ends with `?all` (Neutral)

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
The SPF record's final mechanism is `?all` (neutral qualifier).

### Technical Explanation
`?` qualifier returns neutral for non-matched senders. Zero anti-spoofing enforcement. Should only be used during testing.

### User Explanation
Your domain responds with "we don't know" about unauthorized senders instead of blocking them.

### Recommendation
```
action        : Replace `?all` with `~all` or `-all`.
urgency       : THIS_WEEK
effort        : < 5 MIN
sample_record : v=spf1 include:_spf.google.com ~all
validation_cmd: dig TXT example.com | grep spf
```

### References
- RFC 7208 — Section 4.6.2

---

## SPF-008 — SPF DNS Lookup Limit Exceeded

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
Total DNS lookups to evaluate SPF exceeds 10.

### Detection Logic
SPF evaluator recursively counts all `include:`, `a`, `mx`, `ptr`, `exists` lookups. Total > 10.

### Business Impact
RFC 7208 mandates `permerror` if 10-lookup limit is exceeded. One of the most common SPF failure causes for organizations using multiple ESPs.

### Technical Explanation
Each `include:` costs at least one lookup. Nested includes multiply this. RFC 7208 §4.6.4 requires validators to return `permerror` beyond 10.

### User Explanation
You've listed too many email services in your authorization record. Email providers stop checking after 10 and may fail your emails.

### Recommendation
```
action        : Reduce DNS lookup count below 10 by consolidating or removing includes.
urgency       : IMMEDIATE
effort        : 15–60 MIN
step_by_step  :
  1. List all current include mechanisms and count lookups.
  2. Remove ESPs you no longer use.
  3. Consider SPF flattening (replace includes with direct ip4: ranges).
  4. Verify lookup count drops below 8 for safe headroom.
validation_cmd: dig TXT example.com | grep spf
```

### References
- RFC 7208 — Section 4.6.4

---

## SPF-009 — `include:` Domain Does Not Exist

**Severity:** HIGH | **Weight:** -15 | **Automation:** MANUAL

### Condition
An `include:` mechanism references a domain returning NXDOMAIN.

### Technical Explanation
RFC 7208: `include:` on NXDOMAIN must return `permerror`, causing SPF failure.

### User Explanation
Your authorization record points to an email service domain that no longer exists, breaking your entire SPF setup.

### Recommendation
```
action        : Remove or replace the non-existent `include:` domain.
urgency       : IMMEDIATE
effort        : 5–15 MIN
step_by_step  :
  1. Identify the dead include domain.
  2. Check with your ESP if they have a new SPF include value.
  3. Update or remove the include.
validation_cmd: dig TXT <include_domain>
```

### References
- RFC 7208 — Section 5.2

---

## SPF-010 — `include:` Domain Has No SPF Record

**Severity:** HIGH | **Weight:** -15 | **Automation:** MANUAL

### Condition
An `include:` domain is valid (not NXDOMAIN) but has no `v=spf1` TXT record.

### Technical Explanation
Per RFC 7208, `include:` on a domain with no SPF generates `permerror`. Usually occurs when an ESP changes their SPF include domain.

### User Explanation
Your record points to an email service that hasn't published its own authorization record, breaking your SPF.

### Recommendation
```
action        : Remove the `include:` or contact the ESP for their updated SPF include value.
urgency       : IMMEDIATE
effort        : 5–15 MIN
validation_cmd: dig TXT <include_domain> | grep spf
```

### References
- RFC 7208 — Section 5.2

---

## SPF-011 — SPF Record Too Long

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
SPF record string length exceeds 512 bytes in a single string or 4096 characters total.

### Technical Explanation
DNS UDP responses are limited to 512 bytes. Records exceeding this require TCP fallback, blocked by some networks.

### User Explanation
Your authorization record is unusually long. Some networks can't read it, and long records often signal other problems.

### Recommendation
```
action        : Consolidate SPF record using IP ranges instead of includes where possible.
urgency       : THIS_WEEK
effort        : 15–60 MIN
```

### References
- RFC 7208 — Section 3.3

---

## SPF-012 — SPF Uses Deprecated `ptr` Mechanism

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The SPF record contains a `ptr` mechanism.

### Technical Explanation
RFC 7208 §5.5 explicitly states `ptr` SHOULD NOT be used. It is slow, unreliable, and subject to DNS poisoning.

### User Explanation
Your record uses an outdated method flagged as poor configuration by modern spam filters.

### Recommendation
```
action        : Replace `ptr` with explicit `ip4:` or `ip6:` ranges.
urgency       : THIS_MONTH
effort        : 5–15 MIN
```

### References
- RFC 7208 — Section 5.5

---

## SPF-013 — SPF Lookup Approaching Limit (8–10)

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
SPF lookup count is 8 or 9 — dangerously close to the 10-lookup limit.

### Technical Explanation
Adding any new email service will push the record over the limit and cause `permerror`. Proactive warning to optimize before failure.

### User Explanation
You're close to the maximum number of email services your record can handle. Adding any new service will break SPF.

### Recommendation
```
action        : Reduce SPF lookup count to 6 or fewer for safe headroom.
urgency       : THIS_WEEK
effort        : 15–60 MIN
```

### References
- RFC 7208 — Section 4.6.4

---

## SPF-014 — `redirect=` and `all` Used Together

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
SPF record contains both `redirect=` modifier and an `all` mechanism.

### Technical Explanation
RFC 7208 §6.1: when both are present, `redirect=` is IGNORED. The `all` mechanism takes precedence.

### User Explanation
Your record has conflicting instructions. One is silently ignored, meaning SPF may not work as intended.

### Recommendation
```
action        : Remove either `redirect=` or the `all` mechanism — not both.
urgency       : THIS_WEEK
effort        : < 5 MIN
```

### References
- RFC 7208 — Section 6.1

---

## SPF-015 — Duplicate Mechanisms in SPF Record

**Severity:** LOW | **Weight:** -3 | **Automation:** SEMI_AUTOMATIC

### Condition
SPF record contains identical mechanisms listed more than once.

### Technical Explanation
Duplicate mechanisms waste DNS lookup budget. Each `include:` costs one lookup even when duplicated.

### User Explanation
Your record lists the same permission twice, wasting space and contributing to hitting the service limit.

### Recommendation
```
action        : Remove duplicate mechanisms from the SPF record.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
```

### References
- RFC 7208 — Section 4.6.4

---

## SPF-016 — SPF Has Redundant `ip4:` Ranges

**Severity:** LOW | **Weight:** -3 | **Automation:** SEMI_AUTOMATIC

### Condition
SPF record contains `ip4:` CIDR ranges where one is a superset of another (e.g., `10.0.0.0/8` and `10.1.0.0/24` together).

### Technical Explanation
Redundant CIDR blocks increase record length without providing additional authorization coverage.

### User Explanation
Your record lists some IP addresses twice in different ways, making the record unnecessarily complicated.

### Recommendation
```
action        : Remove redundant ip4: CIDR ranges that are covered by broader ranges.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
```

### References
- RFC 7208 — Section 5.6

---

## SPF-017 — SPF Record Uses Unknown Modifier

**Severity:** INFO | **Weight:** 0 | **Automation:** MANUAL

### Condition
SPF record contains an unknown modifier (not `redirect=` or `exp=`).

### Technical Explanation
RFC 7208 requires validators to silently ignore unknown modifiers. Common mistake: `include` written as `include=` instead of `include:`.

### User Explanation
Your record contains an unrecognized instruction that will be silently ignored — possibly a typo causing a key authorization to be missed.

### Recommendation
```
action        : Review the unknown modifier and correct if it is a typo of a valid mechanism.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
```

### References
- RFC 7208 — Section 6
