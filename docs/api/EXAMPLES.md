# API Reference — Email Deliverability Copilot

**Version:** 1.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Interactive docs:** `http://localhost:8000/docs` (Swagger UI)

> **⚠️ IMPORTANT — Removed Endpoints:** The `POST /api/v1/analysis` endpoint (domain-based DNS analysis, returning `RuleEngineResponse`) **no longer exists**. Examples in the old `EXAMPLES.md` showed `RuleEngineResponse` with `score`, `active_insights`, `business_insights` etc. — this schema is **obsolete**. The current public API is documented below.

---

## Overview

The API has two endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/analysis/headers` | Analyze raw email headers |
| `POST` | `/api/v1/analysis/headers/verify` | Verify DNS records for a domain |
| `GET` | `/` | Health check |

---

## POST /api/v1/analysis/headers

**Purpose:** The primary troubleshooting endpoint. Parses raw email headers, determines SPF/DKIM/DMARC authentication results, computes alignment, identifies the root cause of any failure, and returns ordered remediation steps.

---

### Request

**Content-Type:** `application/json`

**Schema (`HeaderAnalysisRequest`):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `headers` | `string` | ✅ Yes | — | The complete raw email header block. Minimum 1 character, maximum 100,000 characters. |
| `provider_hint` | `string \| null` | No | `null` | Name of the known sending provider. Used to inject provider-specific remediation content. |
| `spf_alignment_mode` | `string` | No | `"relaxed"` | `"relaxed"` or `"strict"`. Controls SPF alignment evaluation. |
| `dkim_alignment_mode` | `string` | No | `"relaxed"` | `"relaxed"` or `"strict"`. Controls DKIM alignment evaluation. |

---

### ⚠️ CRITICAL — How to Format the Request Body

The `headers` field must contain the raw email headers **as a JSON string value**. You do NOT send raw headers directly as the HTTP body.

**Correct:**
```json
{
  "headers": "Delivered-To: user@example.com\nReceived: from mail.example.com...\nAuthentication-Results: mx.google.com; spf=pass ...\nFrom: Alice <alice@example.com>\n"
}
```

**Incorrect (causes HTTP 422):**
```
Delivered-To: user@example.com
Received: from mail.example.com...
Authentication-Results: mx.google.com; spf=pass ...
From: Alice <alice@example.com>
```

Sending raw headers without JSON wrapping returns:
```json
{
  "detail": [
    {
      "type": "json_invalid",
      "msg": "JSON decode error",
      "ctx": { "error": "Expecting property name enclosed in double quotes: line 1 column 1 (char 0)" }
    }
  ]
}
```

This is a **request formatting error**, not an email parsing failure. The eventual frontend will wrap the user's input automatically.

---

### Response

**Status 200 OK**

**Schema (`HeaderAnalysisResponse`):**

```json
{
  "spf": {
    "result": "PASS",
    "raw_result": "pass",
    "domain": "mailer.simplilearn.training",
    "selector": null
  },
  "dkim": {
    "result": "PASS",
    "raw_result": "pass",
    "domain": "simplilearn.training",
    "selector": "ses128"
  },
  "dmarc": {
    "result": "PASS",
    "raw_result": "pass",
    "domain": null,
    "selector": null
  },
  "alignment": {
    "spf": true,
    "dkim": true,
    "overall": true,
    "spf_mode": "relaxed",
    "dkim_mode": "relaxed"
  },
  "from_domain": "simplilearn.training",
  "return_path_domain": "mailer.simplilearn.training",
  "dkim_signing_domain": "simplilearn.training",
  "authentication_results": [
    "mx.google.com; spf=pass smtp.mailfrom=mailer.simplilearn.training; dkim=pass header.d=simplilearn.training header.s=ses128; dmarc=pass header.from=simplilearn.training"
  ],
  "evidence": [
    {
      "authserv_id": "mx.google.com",
      "spf_result": "pass",
      "spf_domain": "mailer.simplilearn.training",
      "dkim_result": "pass",
      "dkim_domain": "simplilearn.training",
      "dkim_selector": "ses128",
      "dmarc_result": "pass",
      "raw": "mx.google.com; spf=pass smtp.mailfrom=mailer.simplilearn.training; ..."
    }
  ],
  "root_cause": null,
  "remediation": [],
  "provider": {
    "name": "Amazon SES",
    "confidence": "MEDIUM"
  },
  "passed": true,
  "failure_summary": null
}
```

**Field Reference:**

| Field | Type | Description |
|-------|------|-------------|
| `spf.result` | `"PASS" \| "FAIL" \| "UNKNOWN"` | Normalized SPF verdict |
| `spf.raw_result` | `string \| null` | Original value from header (e.g., `"softfail"`) |
| `spf.domain` | `string \| null` | SPF-authenticated domain (smtp.mailfrom) |
| `dkim.result` | `"PASS" \| "FAIL" \| "UNKNOWN"` | Normalized DKIM verdict |
| `dkim.domain` | `string \| null` | DKIM signing domain (header.d=) |
| `dkim.selector` | `string \| null` | DKIM selector (header.s=) |
| `dmarc.result` | `"PASS" \| "FAIL" \| "UNKNOWN"` | Normalized DMARC verdict |
| `alignment.spf` | `bool \| null` | SPF alignment — `null` if SPF did not pass |
| `alignment.dkim` | `bool \| null` | DKIM alignment — `null` if DKIM did not pass |
| `alignment.overall` | `bool \| null` | True = DMARC would pass; False = misaligned; null = no data |
| `alignment.spf_mode` | `"relaxed" \| "strict"` | Mode used for SPF alignment check |
| `alignment.dkim_mode` | `"relaxed" \| "strict"` | Mode used for DKIM alignment check |
| `from_domain` | `string \| null` | RFC 5322 From: header domain |
| `return_path_domain` | `string \| null` | Return-Path / envelope-from domain |
| `dkim_signing_domain` | `string \| null` | d= from DKIM-Signature header |
| `authentication_results` | `string[]` | Raw Authentication-Results header strings |
| `evidence` | `AuthEvidence[]` | Parsed authentication evidence per header |
| `root_cause` | `RootCause \| null` | Primary failure cause; null if no failure |
| `root_cause.code` | `string` | Machine-readable code (e.g., `"SPF_AUTH_FAIL"`) |
| `root_cause.title` | `string` | Short human-readable title |
| `root_cause.description` | `string` | Full plain-English explanation |
| `root_cause.protocol` | `"SPF" \| "DKIM" \| "DMARC" \| "NONE"` | Primary protocol involved |
| `remediation` | `RemediationStep[]` | Ordered fix steps; empty if no failure |
| `remediation[].step` | `int` | Step number |
| `remediation[].action` | `string` | Short instruction headline |
| `remediation[].detail` | `string \| null` | Longer explanation |
| `remediation[].sample_record` | `string \| null` | Example DNS record value |
| `remediation[].validation_cmd` | `string \| null` | Shell command to verify the fix |
| `provider` | `ProviderInfo \| null` | Detected sending provider |
| `provider.name` | `string` | Provider name (e.g., `"Amazon SES"`) |
| `provider.confidence` | `"HIGH" \| "MEDIUM" \| "LOW"` | Detection confidence (currently always `"MEDIUM"`) |
| `passed` | `bool` | True if authentication is successful and aligned |
| `failure_summary` | `string \| null` | Short failure title; null if passed |

**`passed` logic:**
```
passed = (spf.result == "PASS" OR dkim.result == "PASS")
         AND alignment.overall == True
         AND dmarc.result != "FAIL"
```

---

### Root Cause Codes

| Code | Title | Protocol | Trigger Condition |
|------|-------|---------|-------------------|
| `NO_HEADERS` | No Authentication Results Found | NONE | No `Authentication-Results` header present |
| `NO_AUTHENTICATION` | No Authentication Performed | NONE | Both SPF and DKIM are UNKNOWN |
| `SPF_AUTH_FAIL` | SPF Authentication Failure | SPF | SPF = FAIL (spf=fail or spf=softfail) |
| `DKIM_AUTH_FAIL` | DKIM Signature Verification Failure | DKIM | DKIM = FAIL |
| `BOTH_ALIGNMENT_FAIL` | SPF and DKIM Alignment Failure | DMARC | Both PASS, both misaligned |
| `SPF_ALIGNMENT_FAIL` | SPF Alignment Failure | SPF | SPF PASS + misaligned; DKIM not available |
| `DKIM_ALIGNMENT_FAIL` | DKIM Alignment Failure | DKIM | DKIM PASS + misaligned; SPF not available |
| `DMARC_POLICY_FAIL` | DMARC Policy Failure | DMARC | Explicit dmarc=fail (catch-all) |

---

### Example Requests and Responses

#### Example 1 — Full Pass (Simplilearn / Amazon SES)

**Request:**
```json
{
  "headers": "From: Simplilearn <no-reply@simplilearn.training>\nReturn-Path: <bounce@mailer.simplilearn.training>\nAuthentication-Results: mx.google.com;\n spf=pass smtp.mailfrom=mailer.simplilearn.training;\n dkim=pass header.d=simplilearn.training header.s=ses128;\n dmarc=pass header.from=simplilearn.training\nDKIM-Signature: v=1; a=rsa-sha256; d=simplilearn.training; s=ses128;\n",
  "provider_hint": "Amazon SES",
  "spf_alignment_mode": "relaxed",
  "dkim_alignment_mode": "relaxed"
}
```

**Response (abbreviated):**
```json
{
  "spf": { "result": "PASS", "raw_result": "pass", "domain": "mailer.simplilearn.training" },
  "dkim": { "result": "PASS", "raw_result": "pass", "domain": "simplilearn.training", "selector": "ses128" },
  "dmarc": { "result": "PASS", "raw_result": "pass" },
  "alignment": { "spf": true, "dkim": true, "overall": true, "spf_mode": "relaxed", "dkim_mode": "relaxed" },
  "from_domain": "simplilearn.training",
  "return_path_domain": "mailer.simplilearn.training",
  "dkim_signing_domain": "simplilearn.training",
  "root_cause": null,
  "remediation": [],
  "provider": { "name": "Amazon SES", "confidence": "MEDIUM" },
  "passed": true,
  "failure_summary": null
}
```

---

#### Example 2 — SPF Authentication Failure

**Request:**
```json
{
  "headers": "From: marketing@example.com\nAuthentication-Results: mx.receiver.com; spf=fail smtp.mailfrom=example.com; dkim=pass header.d=example.com; dmarc=fail\n"
}
```

**Response (abbreviated):**
```json
{
  "spf": { "result": "FAIL", "raw_result": "fail", "domain": "example.com" },
  "dkim": { "result": "PASS", "raw_result": "pass", "domain": "example.com" },
  "dmarc": { "result": "FAIL", "raw_result": "fail" },
  "alignment": { "spf": null, "dkim": true, "overall": true, "spf_mode": "relaxed", "dkim_mode": "relaxed" },
  "from_domain": "example.com",
  "root_cause": {
    "code": "SPF_AUTH_FAIL",
    "title": "SPF Authentication Failure",
    "description": "The receiving server checked the SPF record for 'example.com' and determined that the sending IP address is NOT authorized to send mail for that domain (raw: spf=fail)...",
    "protocol": "SPF"
  },
  "remediation": [
    { "step": 1, "action": "Check your current SPF record for example.com.", "validation_cmd": "dig TXT example.com" },
    { "step": 2, "action": "Identify the IP address of the mail server that sent this email." },
    { "step": 3, "action": "Add your email provider's sending servers to the SPF record.", "sample_record": "v=spf1 include:<your-provider-spf> ~all" },
    ...
  ],
  "passed": false,
  "failure_summary": "SPF Authentication Failure"
}
```

---

#### Example 3 — Both SPF and DKIM Misaligned (SendGrid scenario)

**Request:**
```json
{
  "headers": "From: marketing@example.com\nAuthentication-Results: mx.receiver.com; spf=pass smtp.mailfrom=sendgrid.net; dkim=pass header.d=sendgrid.net; dmarc=fail\n",
  "provider_hint": "SendGrid"
}
```

**Response (abbreviated):**
```json
{
  "spf": { "result": "PASS", "raw_result": "pass", "domain": "sendgrid.net" },
  "dkim": { "result": "PASS", "raw_result": "pass", "domain": "sendgrid.net" },
  "dmarc": { "result": "FAIL", "raw_result": "fail" },
  "alignment": { "spf": false, "dkim": false, "overall": false, "spf_mode": "relaxed", "dkim_mode": "relaxed" },
  "from_domain": "example.com",
  "root_cause": {
    "code": "BOTH_ALIGNMENT_FAIL",
    "title": "SPF and DKIM Alignment Failure",
    "description": "Both SPF and DKIM authentication passed, but neither is aligned with the From domain ('example.com')...",
    "protocol": "DMARC"
  },
  "remediation": [
    { "step": 1, "action": "Understand the problem: both SPF and DKIM passed but neither is aligned with the From domain.", "detail": "From domain: example.com. SPF domain: sendgrid.net. DKIM domain: sendgrid.net. DMARC requires at least one to match." },
    { "step": 2, "action": "Fix DKIM alignment first: configure your email provider to sign with 'example.com'.", "detail": "1. Log in to SendGrid and go to Settings → Sender Authentication.\n2. Click 'Authenticate Your Domain' and follow the setup wizard.\n..." }
  ],
  "passed": false,
  "failure_summary": "SPF and DKIM Alignment Failure"
}
```

---

#### Example 4 — No Authentication-Results Header

**Request:**
```json
{
  "headers": "From: alice@example.com\nSubject: Hello\nDate: Mon, 22 Aug 2026 10:00:00 +0000\n"
}
```

**Response:**
```json
{
  "spf": { "result": "UNKNOWN", "raw_result": null, "domain": null },
  "dkim": { "result": "UNKNOWN", "raw_result": null, "domain": null },
  "dmarc": { "result": "UNKNOWN", "raw_result": null },
  "alignment": { "spf": null, "dkim": null, "overall": null, "spf_mode": "relaxed", "dkim_mode": "relaxed" },
  "from_domain": "example.com",
  "root_cause": {
    "code": "NO_HEADERS",
    "title": "No Authentication Results Found",
    "description": "These headers do not contain an Authentication-Results header...",
    "protocol": "NONE"
  },
  "remediation": [
    { "step": 1, "action": "Retrieve the full raw email headers from the failed message.", "detail": "In Gmail: open the email → click the three-dot menu (⋮) → 'Show original'..." },
    { "step": 2, "action": "Copy ALL headers, including Authentication-Results, Received, DKIM-Signature, and From." },
    { "step": 3, "action": "Paste the complete headers back into the analyzer and resubmit." }
  ],
  "passed": false,
  "failure_summary": "No Authentication Results Found"
}
```

---

### Errors

| Status | Cause |
|--------|-------|
| `422 Unprocessable Entity` | Invalid JSON (e.g., raw headers sent without JSON wrapping), or `headers` field is empty |
| `500 Internal Server Error` | Unexpected server error |

---

## POST /api/v1/analysis/headers/verify

**Purpose:** Perform a live DNS verification to confirm that remediation steps were applied correctly to a domain's DNS records.

---

### Request

**Schema (`VerifyRemediationRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | `string` | ✅ Yes | Domain to verify |
| `selector` | `string \| null` | No | DKIM selector to check (e.g., `"google"`, `"s1"`) |

**Example:**
```json
{
  "domain": "example.com",
  "selector": "google"
}
```

---

### Response

**Schema (`DnsVerificationResult`):**

```json
{
  "analysisId": "uuid",
  "domain": "example.com",
  "status": "completed",
  "timestamp": "2026-08-22T09:00:00Z",
  "dns": {
    "domain": "example.com",
    "lookupStatus": "success",
    "lookupTimeMs": 123,
    "records": { "a": [...], "mx": [...], "txt": [...], ... },
    "errors": []
  },
  "spf": {
    "exists": true,
    "record": "v=spf1 include:_spf.google.com ~all",
    "syntaxValid": true,
    "lookupCount": 1,
    "issues": [],
    "warnings": [],
    "mechanisms": ["include:_spf.google.com", "~all"]
  },
  "dkim": {
    "exists": true,
    "selector": "google",
    "record": "v=DKIM1; k=rsa; p=...",
    "syntaxValid": true,
    "keyType": "rsa",
    "keyLength": 2048,
    "provider": "Google Workspace",
    "status": "VERIFIED",
    "issues": [],
    "warnings": [],
    "tags": {}
  },
  "dmarc": {
    "exists": true,
    "record": "v=DMARC1; p=reject; rua=mailto:dmarc@example.com",
    "syntaxValid": true,
    "policy": "reject",
    "subdomainPolicy": "reject",
    "percentage": 100,
    "alignment": { "dkim": "relaxed", "spf": "relaxed" },
    "reporting": { "rua": ["mailto:dmarc@example.com"], "ruf": [] },
    "issues": [],
    "warnings": [],
    "tags": {}
  }
}
```

### Errors

| Status | Cause |
|--------|-------|
| `400 Bad Request` | Invalid domain format |
| `422 Unprocessable Entity` | Missing required `domain` field |
| `500 Internal Server Error` | DNS resolution or unexpected error |

---

## GET /

**Purpose:** Basic health check confirming the backend is running.

**Response:**
```json
{ "message": "Email Deliverability Copilot backend is running" }
```

---

## Alignment Behavior Reference

| SPF Result | DKIM Result | From Domain | SPF Domain | DKIM Domain | Mode | SPF Aligned | DKIM Aligned | Overall |
|-----------|-------------|-------------|-----------|------------|------|------------|-------------|---------|
| PASS | PASS | example.com | example.com | example.com | relaxed | true | true | true |
| PASS | PASS | example.com | mail.example.com | example.com | relaxed | true | true | true |
| PASS | PASS | example.com | mail.example.com | example.com | strict | false | true | true |
| PASS | PASS | example.com | sendgrid.net | sendgrid.net | relaxed | false | false | false |
| FAIL | PASS | example.com | sendgrid.net | example.com | relaxed | null | true | true |
| PASS | FAIL | example.com | example.com | sendgrid.net | relaxed | true | null | true |
| PASS | PASS | example.com | bounce.example.com | bounce.example.com | strict | false | false | false |

---

*See `app/backend/domains/header_analysis/schemas.py` for the canonical Pydantic schema definitions.*
