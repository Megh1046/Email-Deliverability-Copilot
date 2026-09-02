# System Overview

**Document ID:** ARCH-001

**Version:** 1.0

**Status:** 🟢 LOCKED

**Owner:** Engineering Team

---

# Purpose

This document provides a high-level overview of the Email Deliverability Intelligence Platform architecture.

It explains how each major component interacts and establishes the foundation for implementation.

This document intentionally avoids low-level implementation details. Those belong in API, database, and module specifications.

---

# Architecture Philosophy

The platform follows a modular architecture where each business capability is isolated into its own domain.

The primary design goals are:

- Simplicity
- Scalability
- Maintainability
- AI-friendly development
- Independent feature development

Each module should have a single responsibility and communicate through well-defined interfaces.

---

# High-Level Architecture

```

                    User
                      │
                      ▼
          Next.js Frontend (React)
                      │
              HTTPS REST API
                      │
                      ▼
             FastAPI Backend
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
 Analysis        Automation        AI Assistant
   Domain           Domain            Domain
      │               │                │
      └───────────────┼────────────────┘
                      ▼
                Shared Services
                      │
                      ▼
                 PostgreSQL
                      │
                      ▼
            External Integrations
        (Cloudflare, DNS Providers)

```

---

# System Components

## Frontend

Responsibilities:

- User Interface
- Authentication (future)
- Dashboard
- Analysis Results
- AI Chat
- Reports

Technology:

- Next.js
- React
- TypeScript
- TailwindCSS

---

## Backend

Responsibilities:

- Business Logic
- API
- Authentication Engine
- DNS Analysis
- AI Integration
- Report Generation

Technology:

- FastAPI
- Python

---

## Database

Responsibilities:

- Store analysis history
- Reports
- User settings
- Audit logs (future)

Technology:

- PostgreSQL

---

# Core Domains

## Analysis Domain

Responsible for:

- Email Header Parsing
- SPF Validation
- DKIM Validation
- DMARC Validation
- DNS Lookups
- Confidence Score

---

## Automation Domain

Responsible for:

- DNS Record Generation
- Cloudflare Integration
- DNS Updates
- Verification

---

## Assistant Domain

Responsible for:

- AI Chat
- Authentication Guidance
- Recommendation Generation

---

## Reporting Domain

Responsible for:

- Executive Reports
- Technical Reports
- PDF Export
- JSON Export

---

# External Systems

Version 1 integrates with:

- Cloudflare DNS API
- Public DNS Resolvers
- OpenAI-Compatible AI Provider

Future integrations include:

- AWS Route53
- Google Cloud DNS
- Azure DNS
- Salesforce APIs

---

# Request Lifecycle

A typical request follows this sequence:

1. User submits an email header or domain.
2. Frontend sends the request to the backend.
3. Analysis Domain validates SPF, DKIM, DMARC, and DNS records.
4. Results are scored and interpreted.
5. Explainability logic generates business-friendly recommendations.
6. If requested, Automation Domain prepares or applies DNS changes.
7. Verification confirms successful configuration.
8. Reporting Domain generates downloadable reports.
9. Results are displayed to the user.

---

# Design Principles

- One responsibility per domain.
- Business logic remains in the backend.
- Frontend focuses on presentation.
- APIs define communication.
- External services remain replaceable.
- Automation is optional but preferred.
- Every recommendation must be explainable.

---

# Summary

The architecture is intentionally modular to allow independent development of each domain while maintaining a clean separation of concerns.

This approach supports rapid hackathon development without sacrificing long-term maintainability.
