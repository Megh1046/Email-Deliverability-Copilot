# ARCH-013: Public API Contract Stabilization

## Overview
This architectural decision record outlines the stabilization of the public API contract for the Email Deliverability Copilot, ensuring a consistent and secure external integration surface.

## Decision
1. **RuleEngineResponse as the Sole Public Intelligence Contract:** The `RuleEngineResponse` will serve as the exclusive public contract for returning deliverability intelligence. The fine-grained authentication analysis endpoints (DNS, SPF, DKIM, DMARC) are removed from the public API router.
2. **Internal Use for Granular Responses:** Responses such as `AggregatedAnalysisResponse`, `DnsAnalysisResponse`, `SpfAnalysisResponse`, `DkimAnalysisResponse`, and `DmarcAnalysisResponse` will remain strictly internal for testing, orchestration, and aggregation purposes.
3. **Common API Base:** All public API responses must inherit from the `BaseApiResponse` model, which includes standardized fields: `version`, `timestamp`, and `requestId`. This establishes a foundation for tracking, telemetry, and backward compatibility.

## Rationale
- **Security & Scope:** By restricting the public API to only return the fully evaluated `RuleEngineResponse`, we encapsulate the complexity of the underlying authentication checks. This prevents external consumers from depending on granular internal models that may undergo frequent refactoring.
- **Traceability:** The introduction of `BaseApiResponse` with a `requestId` guarantees end-to-end traceability for every public request, which is critical for debugging and observability in a microservices architecture.
- **Consistency:** Enforcing a single base model guarantees a uniform response shape across any future public endpoints, aligning with industry REST API best practices.

## Consequences
- Existing integrations (if any) relying on the individual `/dns`, `/spf`, `/dkim`, `/dmarc` endpoints will need to migrate to the root `/analysis` endpoint and consume the `RuleEngineResponse` schema.
- Internal tests that previously hit individual public routes have been updated to reflect the new architecture.
- Future public endpoints must inherit from `BaseApiResponse`.
