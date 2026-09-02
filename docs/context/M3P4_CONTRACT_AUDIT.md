# M3P.4 — Frontend/Backend Contract Audit

**Date:** August 2026  
**Document ID:** CTX-006  
**Status:** Complete

---

## 1. Trace of Complete Data Flow

1. **`PageContent.tsx`** triggers `analyzeDomain('mailchimp.com')`.
2. **`api.ts`** executes a `fetch` to `/api/v1/analysis`.
3. **`next.config.ts`** intercepts the request and rewrites it to `http://127.0.0.1:8000/api/v1/analysis`.
4. The request hits a **stale backend process** still lingering on Port 8000 (the active M2F.3 backend is actually running on Port 8001 due to Port 8000 being occupied).
5. The stale backend on Port 8000 returns a Frankenstein JSON response containing a score of 100 (EXCELLENT) alongside contradictory `CRITICAL` active insights and `recommendations` (due to lacking the M2F.1 consistency enforcements).
6. **`PageContent.tsx`** receives the response and runs `getConsistentData()`. Because the score band is `EXCELLENT`, it forcibly filters out all `CRITICAL` and `HIGH` items from the `active_insights` array, leaving only the healthy `INFO` insights. Crucially, it **fails to filter the `recommendations` array**.
7. **`ExecutiveSummary.tsx`** reads `score.band === 'EXCELLENT'` and renders its hardcoded success message: "SPF, DKIM, and DMARC are correctly configured."
8. **`ProtocolHealthCards.tsx`** analyzes the filtered `active_insights` (finding no CRITICAL/HIGH items). It then attempts to read `summary.spf_found` as a fallback. Since the backend `AnalysisSummary` schema changed, this field is `undefined`. The `!fallbackFound` check evaluates to true, forcing **all protocols to render as FAIL**.
9. **`RecommendationsSection.tsx`** receives the unfiltered, contradictory `recommendations` array from the stale backend and dutifully renders "Publish SPF", "Setup DKIM", and "Setup DMARC".

---

## 2. Raw Backend JSON Response (Captured from Port 8000)

```json
{
  "score": {
    "score": 100,
    "band": "EXCELLENT",
    "color": "#22c55e"
  },
  "summary": {
    "status": "critical",
    "errors": 2,
    "warnings": 0,
    "information": 0
  },
  "active_insights": [
    {
      "insight_id": "XPRO-012",
      "severity": "INFO"
    },
    {
      "insight_id": "DMARC-017",
      "severity": "INFO"
    },
    {
      "insight_id": "SPF-001",
      "severity": "CRITICAL"
    }
  ],
  "recommendations": [
    {
      "insight_id": "SPF-001",
      "action": "Publish a valid SPF TXT record..."
    },
    {
      "insight_id": "DKIM-001",
      "action": "Generate a DKIM key pair..."
    }
  ]
}
```

---

## 3. UI Values Comparison

| Component | Expected UI Value (based on 100/EXCELLENT) | Actual UI Value | Cause |
|-----------|------------------------------------------|-----------------|-------|
| **ScoreDisplay** | 100 / EXCELLENT | 100 / EXCELLENT | Pulls directly from `score.band` |
| **ExecutiveSummary** | "SPF, DKIM, DMARC are healthy" | "SPF, DKIM, DMARC are healthy" | Hardcoded string based on `score.band === 'EXCELLENT'` |
| **InsightsSection** | Only healthy insights | Only healthy insights | `PageContent.tsx` artificially filters out CRITICAL insights when score is EXCELLENT. |
| **ProtocolHealthCards** | PASS / PASS / PASS / PASS | FAIL / FAIL / FAIL / FAIL | Schema mismatch on `summary` object forces `!fallbackFound` to trigger. |
| **RecommendationsSection** | Empty (No recommendations) | Publish SPF, Setup DKIM | `PageContent.tsx` fails to filter recommendations when filtering active insights, leaking the stale backend's contradictions. |

---

## 4. Schema Mismatches

The frontend interface `RuleEngineResponse` and its mock `mockRuleEngineResponse` are severely outdated compared to the actual backend `schemas.py`.

**Frontend Expectation (`types/analysis.ts` & `ProtocolHealthCards.tsx`):**
```typescript
summary: {
  dns_resolved: boolean;
  spf_found: boolean;
  dkim_found: boolean;
  dmarc_found: boolean;
}
```

**Actual Backend Response (`app/backend/domains/analysis/schemas.py`):**
```python
class AnalysisSummary(BaseModel):
    status: str
    errors: int
    warnings: int
    information: int
```

---

## 5. Root Cause Determination

The bug is a catastrophic combination of:
1. **Stale Port Configuration:** `next.config.ts` points to `8000` instead of `8001`.
2. **Stale Mock Assumptions (Schema Mismatch):** The frontend expects boolean flags in the `summary` object that no longer exist in the backend schema.
3. **Protocol Status Calculation Error:** `ProtocolHealthCards.tsx` uses falsy evaluation (`!fallbackFound`) on the missing boolean fields, causing healthy protocols to default to `FAIL`.
4. **Incomplete Normalization Logic:** `PageContent.tsx` implements a dangerous "Consistency Layer" that filters `active_insights` to hide backend contradictions, but forgets to filter the `recommendations` array alongside it.

---

## 6. Exact Files Requiring Modification

1. **`app/frontend/next.config.ts`**: Update the proxy destination to `http://127.0.0.1:8001/api/:path*`.
2. **`app/frontend/src/types/analysis.ts`**: Update the `AnalysisSummary` interface to match the backend (`status`, `errors`, `warnings`, `information`).
3. **`app/frontend/src/components/ProtocolHealthCards.tsx`**: Rewrite the `determineStatus` calculation to stop relying on the removed boolean fallback flags. It must calculate status solely based on the presence/absence of CRITICAL/HIGH/MEDIUM insights for that protocol.
4. **`app/frontend/src/app/PageContent.tsx`**: Remove the `getConsistentData()` consistency layer entirely. The M2F.1 backend already enforces strict consistency (ARCH-015). Masking backend outputs in the frontend creates diverging states and hides real bugs.
