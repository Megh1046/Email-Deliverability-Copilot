# Email Deliverability Copilot

An AI-assisted email authentication and deliverability platform. Paste raw email headers from any delivered email and get an instant, plain-English diagnosis of SPF, DKIM, and DMARC failures, alignment issues, and step-by-step provider-specific remediation instructions.

---

## 🚀 Current Project Status

Both the **Backend API** and **Frontend Web Application** are fully operational!

| Component | Status | Tech Stack / Details |
|-----------|--------|----------------------|
| **Frontend Web App** | ✅ Operational | Next.js 16, React 19, TypeScript, Tailwind CSS v4, Framer Motion |
| **Header Analysis API** (`POST /api/v1/analysis/headers`) | ✅ Operational | FastAPI, Python 3.11+, Uvicorn, Pydantic |
| **DNS Verification API** (`POST /api/v1/analysis/headers/verify`) | ✅ Operational | FastAPI, dnspython, custom DNS resolver |
| **RFC 8601 Header Parser & Auth Extractor** | ✅ Operational | Extracts SPF, DKIM, DMARC verdicts & signing domains |
| **RFC 7489 Alignment Engine** | ✅ Operational | Supports relaxed & strict alignment modes |
| **8-Case Root Cause Engine** | ✅ Operational | Priority decision tree for failure diagnosis |
| **Provider-Aware Remediation** | ✅ Operational | Tailored guides for Google Workspace, Microsoft 365, SES, SendGrid, Mailchimp, etc. |

---

## ✨ Features

- 🔍 **5-Stage Analysis Pipeline**: Parses raw email headers, normalizes verdicts, checks domain alignment, pinpoints root causes, and generates actionable remediation.
- 🎨 **Modern React 19 Frontend**: Features a polished UI with interactive sample headers, step-by-step diagnostic breakdown, copyable DNS fix records, and raw header inspectors.
- ⚡ **DNS Verification Engine**: Perform live DNS lookups to verify SPF, DKIM, and DMARC TXT records against domain DNS servers.
- 🛡️ **Provider Fingerprinting & Guides**: Detects sending infrastructure (Google Workspace, Microsoft 365, Amazon SES, SendGrid, Mailchimp, Mailgun, Zendesk) and provides exact DNS record templates.
- 📋 **Flexible Alignment Modes**: Analyze domain alignment in both `relaxed` (subdomain allowed) and `strict` (exact match) modes.

---

## 🏗️ Project Architecture

```
Email-Deliverability-Copilot/
├── app/
│   ├── backend/               # FastAPI Backend Service
│   │   ├── main.py            # Application entrypoint & FastAPI routes
│   │   ├── domains/
│   │   │   ├── header_analysis/ # 5-Stage Header Analysis Pipeline
│   │   │   ├── dns/            # Live DNS Resolver & Record Verifiers
│   │   │   └── remediation/    # Provider-specific remediation guides
│   │   └── tests/             # Backend test suite
│   │
│   └── frontend/              # Next.js Frontend Application
│       ├── src/
│       │   ├── app/           # Next.js App Router (Page & Layout)
│       │   ├── components/    # UI Components (AnalysisResults, RootCause, etc.)
│       │   └── services/      # API Integration Service (`header-api.ts`)
│       ├── package.json
│       └── next.config.ts
├── docs/                      # Extensive Architecture & Product Documentation
└── scripts/                   # Utility scripts
```

---

## ⚡ Quick Start

### 1. Run the Backend API

```bash
# Navigate to the backend directory
cd app/backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI dev server
uvicorn main:app --reload
```
The backend server will run at `http://localhost:8000`.  
Swagger UI documentation is available at `http://localhost:8000/docs`.

### 2. Run the Frontend Web Application

```bash
# Navigate to the frontend directory
cd app/frontend

# Install Node dependencies
npm install

# Start the Next.js development server
npm run dev
```
The frontend application will be live at `http://localhost:3000`.

---

## 📡 API Reference

### 1. Analyze Email Headers

**Endpoint:** `POST /api/v1/analysis/headers`

**Request Body:**
```json
{
  "headers": "From: sender@example.com\nReturn-Path: <bounce@example.com>\nAuthentication-Results: mx.google.com; spf=pass smtp.mailfrom=bounce.example.com; dkim=pass header.d=example.com; dmarc=pass\n",
  "spf_alignment_mode": "relaxed",
  "dkim_alignment_mode": "relaxed",
  "provider_hint": "Google Workspace"
}
```

**Response Overview (`HeaderAnalysisResponse`):**
- `spf`, `dkim`, `dmarc`: Protocol status (`PASS`, `FAIL`, `UNKNOWN`), domains, and selectors.
- `alignment`: Overall alignment boolean, SPF alignment, DKIM alignment.
- `root_cause`: Primary failure code, title, and detailed explanation.
- `remediation`: Ordered list of actionable steps with sample records and validation commands.
- `passed`: Boolean indicator if email passed all deliverability checks.

### 2. Verify DNS Records

**Endpoint:** `POST /api/v1/analysis/headers/verify`

**Request Body:**
```json
{
  "domain": "example.com",
  "selector": "google"
}
```

---

## 🧪 Running Tests

### Backend Tests
```bash
cd app/backend
pytest tests/ -v
```

---

## 📖 Documentation

- [`docs/context/PROJECT_CONTEXT.md`](docs/context/PROJECT_CONTEXT.md) — Architectural overview, data flows, and domain models
- [`docs/context/CURRENT_STATE.md`](docs/context/CURRENT_STATE.md) — Detailed feature status & implementation notes
- [`docs/context/DECISIONS.md`](docs/context/DECISIONS.md) — Architectural decision log
- [`docs/api/EXAMPLES.md`](docs/api/EXAMPLES.md) — Comprehensive API payloads and response schemas

---

## 📄 License

MIT License

