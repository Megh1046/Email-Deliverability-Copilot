# DKIM Insights

**Document ID:** DKB-003  
**Version:** 1.0  
**Status:** 🟡 IN PROGRESS  
**Last Updated:** July 2026  
**Protocol:** DKIM  
**Total Insights:** 17

---

## Summary Table

| ID | Title | Severity | Automation |
|---|---|---|---|
| DKIM-001 | No DKIM Record Found for Selector | CRITICAL | SEMI_AUTOMATIC |
| DKIM-002 | DKIM Public Key Missing or Empty | CRITICAL | SEMI_AUTOMATIC |
| DKIM-003 | DKIM Record Missing `p=` Tag | CRITICAL | SEMI_AUTOMATIC |
| DKIM-004 | DKIM Key Revoked (`p=` is empty string) | CRITICAL | SEMI_AUTOMATIC |
| DKIM-005 | DKIM Record Not Parseable (Malformed TXT) | CRITICAL | SEMI_AUTOMATIC |
| DKIM-006 | DKIM Key Too Short (< 1024 bits) | CRITICAL | SEMI_AUTOMATIC |
| DKIM-007 | DKIM Key Exactly 1024 bits (Weak) | HIGH | SEMI_AUTOMATIC |
| DKIM-008 | DKIM Version Tag Incorrect | HIGH | SEMI_AUTOMATIC |
| DKIM-009 | DKIM `h=` Tag Restricts Hash to SHA-1 | HIGH | SEMI_AUTOMATIC |
| DKIM-010 | Multiple DKIM Records for Same Selector | HIGH | MANUAL |
| DKIM-011 | DKIM Key Base64 Encoding Invalid | HIGH | SEMI_AUTOMATIC |
| DKIM-012 | DKIM Record Has Unknown or Invalid Tags | MEDIUM | MANUAL |
| DKIM-013 | DKIM Record Has Duplicate Tags | MEDIUM | SEMI_AUTOMATIC |
| DKIM-014 | DKIM `s=` Tag Incorrectly Restricts Service | MEDIUM | SEMI_AUTOMATIC |
| DKIM-015 | DKIM `t=y` Testing Mode Active in Production | MEDIUM | SEMI_AUTOMATIC |
| DKIM-016 | DKIM `t=s` Strict Subdomaining Misconfigured | LOW | SEMI_AUTOMATIC |
| DKIM-017 | DKIM `k=` Key Type Not Specified | LOW | SEMI_AUTOMATIC |

---

## DKIM-001 — No DKIM Record Found for Selector

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
No DKIM TXT record exists at the selector subdomain (`<selector>._domainkey.<domain>`).

### Detection Logic
DNS resolver returns NXDOMAIN or no TXT answer for the DKIM selector query.

### Business Impact
Without DKIM, email bodies and headers are unsigned. DMARC authentication based on DKIM alignment fails. Gmail, Outlook, and Yahoo downgrade or reject unsigned messages.

### Technical Explanation
RFC 6376 requires a TXT record at `<selector>._domainkey.<domain>` containing the public key. Without it, DKIM verification fails for every message claiming to use that selector.

### User Explanation
Your emails don't have a digital signature configured. Email providers check for this signature to verify your emails haven't been tampered with. Without it, your emails are more likely to be marked as spam.

### Recommendation
```
action        : Generate a DKIM key pair and publish the public key as a TXT record.
urgency       : IMMEDIATE
effort        : 15–60 MIN
sample_record : v=DKIM1; k=rsa; p=<base64_public_key>
step_by_step  :
  1. Generate a 2048-bit RSA key pair using your ESP or openssl.
  2. Publish the public key as a TXT record at: <selector>._domainkey.<domain>
  3. Configure your mail server or ESP to sign outbound mail with the private key.
  4. Send a test email and verify DKIM pass in the headers.
validation_cmd: dig TXT <selector>._domainkey.example.com
```

### References
- RFC 6376 — DomainKeys Identified Mail

---

## DKIM-002 — DKIM Public Key Missing or Empty

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record exists but the `p=` tag value is absent (not present, no value at all — distinct from empty string revocation).

### Detection Logic
DKIM parser finds a TXT record at the selector path but the `p=` tag is missing from the tag list.

### Technical Explanation
RFC 6376 §3.6.1: the `p=` tag is required. A record without it is syntactically invalid and will cause DKIM verification failure.

### User Explanation
Your email signature record exists but is missing the actual signature key. Emails cannot be validated.

### Recommendation
```
action        : Regenerate and republish the DKIM public key ensuring `p=` is included.
urgency       : IMMEDIATE
effort        : 15–60 MIN
sample_record : v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3...
validation_cmd: dig TXT <selector>._domainkey.example.com
```

### References
- RFC 6376 — Section 3.6.1

---

## DKIM-003 — DKIM Record Missing `p=` Tag

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
The `p=` tag is completely absent from the DKIM TXT record (not empty, just not present).

### Detection Logic
DKIM parser processes the TXT record tag-value list and finds no `p` key.

### Technical Explanation
Same as DKIM-002 but distinguished by the case where the tag is entirely absent vs. having an empty value. Without `p=`, the record cannot serve as a public key source.

### User Explanation
Your digital signature record is missing its most critical field — the key itself. Email verification cannot be performed.

### Recommendation
```
action        : Add the `p=` tag with the base64-encoded public key to the DKIM record.
urgency       : IMMEDIATE
effort        : 15–60 MIN
validation_cmd: dig TXT <selector>._domainkey.example.com
```

### References
- RFC 6376 — Section 3.6.1

---

## DKIM-004 — DKIM Key Revoked (`p=` is Empty String)

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record exists and the `p=` tag is present with an empty value (`p=`).

### Detection Logic
DKIM parser finds `p=` tag with zero-length value.

### Business Impact
RFC 6376 defines an empty `p=` value as a deliberate key revocation signal. All email signed with this selector will fail DKIM verification.

### Technical Explanation
An empty `p=` is the RFC-approved method to revoke a DKIM key — signaling that the key has been compromised or retired. Any existing signed mail is now unverifiable.

### User Explanation
Your email signature key has been deliberately disabled or revoked. No emails can be verified with this key until a new one is published.

### Recommendation
```
action        : Generate a new DKIM key pair and publish the new public key.
urgency       : IMMEDIATE
effort        : 15–60 MIN
sample_record : v=DKIM1; k=rsa; p=<new_base64_public_key>
step_by_step  :
  1. Generate a new 2048-bit RSA key pair.
  2. Replace the revoked record with the new public key.
  3. Update your mail server configuration with the new private key.
validation_cmd: dig TXT <selector>._domainkey.example.com
```

### References
- RFC 6376 — Section 3.6.1 (key revocation)

---

## DKIM-005 — DKIM Record Not Parseable

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
A TXT record exists at the DKIM selector path but cannot be parsed as valid DKIM tag-value format.

### Detection Logic
DKIM parser encounters a TXT record that does not conform to the `tag=value; tag=value` format.

### Technical Explanation
RFC 6376 §3.6 requires DKIM records to follow strict tag-value list format: `tag=value` pairs separated by semicolons. A malformed record prevents key retrieval.

### User Explanation
Your email signature record exists but is corrupted or improperly formatted. Email providers cannot read it.

### Recommendation
```
action        : Delete and republish a correctly formatted DKIM record.
urgency       : IMMEDIATE
effort        : 15–60 MIN
sample_record : v=DKIM1; k=rsa; p=<base64_key>
validation_cmd: dig TXT <selector>._domainkey.example.com
```

### References
- RFC 6376 — Section 3.6

---

## DKIM-006 — DKIM Key Too Short (< 1024 bits)

**Severity:** CRITICAL | **Weight:** -25 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM RSA public key has a key length less than 1024 bits.

### Detection Logic
DKIM validator decodes the base64 `p=` value and checks the RSA key modulus length.

### Business Impact
RFC 8301 deprecates DKIM keys below 1024 bits. Gmail and other major providers reject messages signed with sub-1024-bit keys.

### Technical Explanation
Keys below 1024 bits are cryptographically weak and considered insecure. RFC 8301 §3.2 requires key length of at least 1024 bits.

### User Explanation
Your email digital signature uses an outdated, insecure key that is too short to be trusted. Major email providers will reject emails signed with it.

### Recommendation
```
action        : Generate a new 2048-bit DKIM key pair immediately.
urgency       : IMMEDIATE
effort        : 15–60 MIN
step_by_step  :
  1. Generate a new 2048-bit RSA key pair.
  2. Publish the new public key at your DKIM selector.
  3. Update your mail server with the new private key.
  4. Verify DKIM pass in test email headers.
validation_cmd: dig TXT <selector>._domainkey.example.com
```

### References
- RFC 8301 — Cryptographic Algorithm and Key Usage Update to DKIM

---

## DKIM-007 — DKIM Key Exactly 1024 bits (Weak — Upgrade Recommended)

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM RSA public key is exactly 1024 bits.

### Detection Logic
DKIM validator decodes `p=` and measures RSA key modulus at exactly 1024 bits.

### Business Impact
1024-bit RSA keys meet the RFC 8301 minimum but are considered cryptographically weak by current standards. Google announced phasing out 1024-bit DKIM keys. Proactive upgrade is recommended.

### Technical Explanation
RFC 8301 §3.2 sets the minimum at 1024 bits but recommends 2048 bits. 1024-bit RSA is susceptible to factoring attacks. Upgrade to 2048 bits before enforcement deadlines.

### User Explanation
Your email digital signature uses a key that meets minimum requirements but is considered weak by modern standards. Upgrading it will improve your email security and sender reputation.

### Recommendation
```
action        : Upgrade DKIM key from 1024 to 2048 bits.
urgency       : THIS_MONTH
effort        : 15–60 MIN
step_by_step  :
  1. Generate a new 2048-bit RSA key pair.
  2. Publish the new public key at a new or updated DKIM selector.
  3. Update your mail server to sign with the new private key.
  4. Deprecate the old 1024-bit key after confirming the new key is working.
```

### References
- RFC 8301 — Section 3.2

---

## DKIM-008 — DKIM Version Tag Incorrect

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record contains a `v=` tag with a value other than `DKIM1`.

### Detection Logic
DKIM parser finds `v=` tag. Value is not exactly `DKIM1`.

### Technical Explanation
RFC 6376 §3.6.1 specifies that if `v=` is present it MUST be `DKIM1`. Any other value causes the record to be treated as invalid.

### User Explanation
Your email signature record has an incorrect version tag that may cause some email providers to reject it.

### Recommendation
```
action        : Correct the `v=` tag value to exactly `DKIM1`.
urgency       : THIS_WEEK
effort        : < 5 MIN
sample_record : v=DKIM1; k=rsa; p=<key>
validation_cmd: dig TXT <selector>._domainkey.example.com
```

### References
- RFC 6376 — Section 3.6.1

---

## DKIM-009 — DKIM `h=` Tag Restricts Hash to SHA-1

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record contains `h=sha1` restricting hash algorithms to SHA-1 only.

### Detection Logic
DKIM parser finds `h=` tag. Value contains only `sha1` with no `sha256`.

### Business Impact
SHA-1 is cryptographically broken and deprecated for DKIM. RFC 8301 requires SHA-256 support. Verifiers may reject SHA-1-only configurations.

### Technical Explanation
RFC 8301 §3.1 removes SHA-1 (sha1) support from DKIM. Specifying `h=sha1` alone means the signing server will only use SHA-1 hashes, which may be rejected by compliant verifiers.

### User Explanation
Your email signature record limits signatures to a broken, outdated hashing algorithm. Modern email providers may reject these signatures.

### Recommendation
```
action        : Remove `h=sha1` restriction or update to `h=sha256`.
urgency       : THIS_WEEK
effort        : < 5 MIN
sample_record : v=DKIM1; k=rsa; h=sha256; p=<key>
```

### References
- RFC 8301 — Section 3.1

---

## DKIM-010 — Multiple DKIM Records for Same Selector

**Severity:** HIGH | **Weight:** -15 | **Automation:** MANUAL

### Condition
Two or more TXT records exist at the same DKIM selector path.

### Detection Logic
DNS resolver returns multiple TXT records at `<selector>._domainkey.<domain>`.

### Technical Explanation
A DKIM selector path must have exactly one TXT record. Multiple records cause verifier ambiguity and are treated as configuration errors by most implementations.

### User Explanation
You have two signature records for the same email identity. Email providers can't determine which one to use, causing verification to fail.

### Recommendation
```
action        : Delete all but one TXT record at the DKIM selector path.
urgency       : IMMEDIATE
effort        : 5–15 MIN
step_by_step  :
  1. Identify all TXT records at the selector path.
  2. Determine which record contains the active public key.
  3. Delete all others.
validation_cmd: dig TXT <selector>._domainkey.example.com
```

### References
- RFC 6376 — Section 3.6

---

## DKIM-011 — DKIM Key Base64 Encoding Invalid

**Severity:** HIGH | **Weight:** -15 | **Automation:** SEMI_AUTOMATIC

### Condition
The `p=` tag value in the DKIM record fails base64 decoding.

### Detection Logic
DKIM validator attempts base64 decode of the `p=` value and receives a decode error.

### Technical Explanation
RFC 6376 specifies the public key must be base64-encoded per RFC 4648. An invalid base64 value prevents key extraction and causes DKIM failure.

### User Explanation
Your email signature key contains a formatting error and cannot be read by email providers.

### Recommendation
```
action        : Regenerate and republish the DKIM key ensuring the public key is correctly base64-encoded.
urgency       : IMMEDIATE
effort        : 15–60 MIN
```

### References
- RFC 6376 — Section 3.6.1, RFC 4648

---

## DKIM-012 — DKIM Record Has Unknown or Invalid Tags

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** MANUAL

### Condition
DKIM record contains tag names not defined by RFC 6376 (not `v`, `g`, `h`, `k`, `n`, `p`, `s`, `t`).

### Detection Logic
DKIM parser encounters tag names not in the standard tag set.

### Technical Explanation
RFC 6376 §3.6.1 allows unknown tags to be ignored, but their presence usually indicates typos or garbage publication. Commonly a sign of incomplete ESP configuration.

### User Explanation
Your signature record contains unrecognized fields. While they may not break delivery, they suggest a misconfiguration.

### Recommendation
```
action        : Review and remove unknown tags from the DKIM record.
urgency       : WHEN_POSSIBLE
effort        : 5–15 MIN
```

### References
- RFC 6376 — Section 3.6.1

---

## DKIM-013 — DKIM Record Has Duplicate Tags

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record contains the same tag name more than once.

### Detection Logic
DKIM parser builds a tag map and detects duplicate key entries.

### Technical Explanation
RFC 6376 §3.6.1 specifies that tag names MUST NOT appear more than once. A record with duplicate tags is considered malformed.

### User Explanation
Your email signature record lists the same field twice, making the record malformed and potentially causing verification failures.

### Recommendation
```
action        : Remove duplicate tags from the DKIM record, keeping one of each.
urgency       : THIS_WEEK
effort        : < 5 MIN
```

### References
- RFC 6376 — Section 3.6.1

---

## DKIM-014 — DKIM `s=` Tag Incorrectly Restricts Service Type

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record's `s=` tag has a value that does not include `email` or `*`.

### Detection Logic
DKIM parser evaluates `s=` tag value. The colon-separated list does not contain `email` or `*`.

### Technical Explanation
The `s=` tag restricts which services can use this key. If it doesn't include `email` or `*`, the key cannot legally be used for email signing.

### User Explanation
Your signature key is configured to only be used for specific services, and email may not be one of them.

### Recommendation
```
action        : Set `s=email` or `s=*` in the DKIM record to allow email signing.
urgency       : THIS_WEEK
effort        : < 5 MIN
sample_record : v=DKIM1; k=rsa; s=email; p=<key>
```

### References
- RFC 6376 — Section 3.6.1 (`s=` tag)

---

## DKIM-015 — DKIM `t=y` Testing Mode Active in Production

**Severity:** MEDIUM | **Weight:** -8 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record contains `t=y` flag.

### Detection Logic
DKIM parser finds `t=` tag. Value is `y` or includes `y`.

### Business Impact
`t=y` signals to verifiers that the domain is testing DKIM. Per RFC 6376, verifiers SHOULD treat messages as if they have no DKIM signature when `t=y` is set. This effectively disables DKIM enforcement.

### Technical Explanation
The `t=y` flag indicates the signing domain does not want verifiers to reject or down-classify mail on DKIM failure. It is a test mode that has no place in production configurations.

### User Explanation
Your email signature is set to "testing mode." Email providers are treating your signatures as if they don't exist. This needs to be changed for signatures to be enforced.

### Recommendation
```
action        : Remove the `t=y` flag from your DKIM record.
urgency       : THIS_WEEK
effort        : < 5 MIN
sample_record : v=DKIM1; k=rsa; p=<key>
```

### References
- RFC 6376 — Section 3.6.1 (`t=` tag flags)

---

## DKIM-016 — DKIM `t=s` Strict Subdomaining Misconfigured

**Severity:** LOW | **Weight:** -3 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record contains `t=s` flag, but email is being sent from subdomains.

### Detection Logic
DKIM parser finds `t=s` in the `t=` tag. Cross-check with observed sending domain: if subdomain email is expected, this is a conflict.

### Technical Explanation
The `t=s` flag prevents the key from being used to sign email where the `i=` identity is a subdomain of the `d=` signing domain. If subdomain sending is intended, this flag restricts it.

### User Explanation
Your signature record has a restriction that may prevent emails from your subdomains from being signed correctly.

### Recommendation
```
action        : Remove `t=s` from the DKIM record if subdomain signing is required.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
```

### References
- RFC 6376 — Section 3.6.1

---

## DKIM-017 — DKIM `k=` Key Type Not Specified

**Severity:** LOW | **Weight:** -3 | **Automation:** SEMI_AUTOMATIC

### Condition
The DKIM record does not contain a `k=` tag specifying the key type.

### Detection Logic
DKIM parser finds no `k=` tag in the record.

### Technical Explanation
RFC 6376 §3.6.1 specifies that if `k=` is absent, RSA is the default. While this is technically valid, omitting it is poor hygiene and causes ambiguity when newer key types (like `k=ed25519`) become standard.

### User Explanation
Your signature record is missing a field that specifies what type of encryption key you're using. While it defaults to the standard type, it's cleaner to make it explicit.

### Recommendation
```
action        : Add `k=rsa` explicitly to the DKIM record for clarity.
urgency       : WHEN_POSSIBLE
effort        : < 5 MIN
sample_record : v=DKIM1; k=rsa; p=<key>
```

### References
- RFC 6376 — Section 3.6.1 (`k=` tag)
