# Deliverability Knowledge Base (DKB)

Version: 1.0
Status: Draft
Owner: Email Deliverability Copilot

---

# Purpose

The Deliverability Knowledge Base (DKB) is the canonical repository of deliverability expertise used by every intelligent component of the system.

It is the single source of truth for:

- Rule Engine
- Recommendation Engine
- Confidence Score
- AI Assistant
- Automation Engine
- Reporting

Protocol validators (DNS, SPF, DKIM, DMARC) only collect facts.

The DKB converts those facts into actionable intelligence.

---

# Rule Format

Every rule follows the same structure.

Rule ID
Title
Category
Severity
Condition
Detection Logic
Business Impact
Technical Explanation
User Explanation
Recommendation
Automation Available
Confidence Weight
Dependencies
References

---

# Severity Levels

Critical
High
Medium
Low
Information

---

# Categories

DNS

SPF

DKIM

DMARC

Authentication

Alignment

DNS Health

Deliverability

Domain Reputation

Configuration

Automation

Verification

Security

Reporting

---

# Confidence Weight

Every rule contributes positively or negatively to the Deliverability Confidence Score.

Example

Critical = -25

High = -15

Medium = -8

Low = -3

Information = 0

---

# Automation Levels

Automatic

Semi-Automatic

Manual

Not Possible

---

# Rule Template

## Rule ID

R001

### Title

Missing SPF Record

### Category

SPF

### Severity

Critical

### Condition

No SPF TXT record exists.

### Detection Logic

SPF validator returns exists = false.

### Business Impact

Mailbox providers cannot verify which servers are allowed to send email.

### Technical Explanation

Without SPF, sender authentication is incomplete.

### User Explanation

Your domain doesn't tell email providers who is allowed to send emails.

### Recommendation

Publish a valid SPF TXT record.

### Automation

Semi-Automatic

Generate SPF DNS record.

### Confidence Weight

-25

### References

RFC 7208

---