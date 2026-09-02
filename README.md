# Email Deliverability Copilot

An email authentication troubleshooter. Paste raw email headers and get a plain-English diagnosis of SPF, DKIM, and DMARC authentication failures, with step-by-step remediation instructions.

---

## What It Does

1. **Paste** raw email headers (from Gmail, Outlook, Apple Mail, etc.)
2. **Get** a clear diagnosis: which protocol failed, why it failed, what it means
3. **Follow** actionable remediation steps (provider-specific when the provider is known)
4. **Verify** that fixes were applied correctly by re-analyzing updated headers

---

## Current Status

The backend API is operational. No frontend UI exists yet.

| Component | Status |
|-----------|--------|
| Backend API (`POST /api/v1/analysis/headers`) | ✅ Working |
| DNS Verification (`POST /api/v1/analysis/headers/verify`) | ✅ Working |
| Frontend UI | ❌ Not started |
| Database | ❌ Not started |

---

## Quick Start (Backend)

### Prerequisites

- Python 3.11+
- pip

### Install and Run

```bash
# From the repository root
cd app/backend

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn main:app --reload

# API is now running at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

---

## Analyze Email Headers

The API accepts raw email headers as a JSON string.

**To analyze headers via curl:**

```bash
curl -X POST http://localhost:8000/api/v1/analysis/headers \
  -H "Content-Type: application/json" \
  -d '{
    "headers": "From: alice@example.com\nReturn-Path: <bounce@example.com>\nAuthentication-Results: mx.google.com; spf=pass smtp.mailfrom=bounce.example.com; dkim=pass header.d=example.com; dmarc=pass\n",
    "spf_alignment_mode": "relaxed",
    "dkim_alignment_mode": "relaxed"
  }'
```

> **Note:** The raw email headers must be a JSON string (embedded inside `"headers": "..."`). Do NOT paste raw headers directly as the HTTP body — this causes a 422 error.

**How to get raw headers from your email client:**
- **Gmail:** Open email → three-dot menu (⋮) → "Show original"
- **Outlook:** Open email → File → Properties → Internet headers
- **Apple Mail:** View → Message → All Headers

---

## Run Tests

```bash
cd app/backend
pytest tests/ -v
```

> **Note:** Several test files reference modules from the previous architecture that have been replaced. Not all tests may pass. See `docs/context/CURRENT_STATE.md` for details.

---

## Project Documentation

- [`docs/context/PROJECT_CONTEXT.md`](docs/context/PROJECT_CONTEXT.md) — Architecture, API, data flow, all module descriptions
- [`docs/context/CURRENT_STATE.md`](docs/context/CURRENT_STATE.md) — What is working right now
- [`docs/context/DECISIONS.md`](docs/context/DECISIONS.md) — Architectural decision log
- [`docs/context/NEXT_TASK.md`](docs/context/NEXT_TASK.md) — Implementation priorities
- [`docs/context/CHANGELOG.md`](docs/context/CHANGELOG.md) — Change history
- [`docs/api/EXAMPLES.md`](docs/api/EXAMPLES.md) — API reference with request/response examples

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/v1/analysis/headers` | Analyze raw email headers |
| `POST` | `/api/v1/analysis/headers/verify` | Verify DNS records for a domain |

---

## License

MIT
