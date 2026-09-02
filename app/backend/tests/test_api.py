"""
API endpoint tests (M2F-updated)

Validates:
- POST /api/v1/analysis accepts FullAnalysisRequest
- Response conforms to RuleEngineResponse (BaseApiResponse contract)
- IntelligenceOrchestrator is the integration point (mocked via aggregator)
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
from domains.analysis.aggregator.schemas import AggregatedAnalysisResponse, AnalysisSummary
from domains.analysis.schemas import (
    DnsAnalysisResponse, SpfResult, DkimResult, DmarcResult,
    DmarcAlignment, DmarcReporting
)

client = TestClient(app)


def make_healthy_aggregated_response() -> AggregatedAnalysisResponse:
    return AggregatedAnalysisResponse(
        analysisId="abc-123",
        domain="example.com",
        status="completed",
        timestamp="2026-07-29T00:00:00Z",
        dns=DnsAnalysisResponse(
            domain="example.com", lookupStatus="success",
            lookupTimeMs=10, records={}, errors=[]
        ),
        spf=SpfResult(
            exists=True, record="v=spf1 ~all", syntaxValid=True,
            lookupCount=0, issues=[], warnings=[], mechanisms=[]
        ),
        dkim=DkimResult(
            exists=True, selector="s1", record="v=DKIM1;",
            syntaxValid=True, keyType="rsa", issues=[], warnings=[], tags={}
        ),
        dmarc=DmarcResult(
            exists=True, record="v=DMARC1; p=reject;", syntaxValid=True,
            policy="reject", subdomainPolicy="reject", percentage=100,
            alignment=DmarcAlignment(dkim="r", spf="r"),
            reporting=DmarcReporting(rua=[], ruf=[]),
            issues=[], warnings=[], tags={}
        ),
        summary=AnalysisSummary(status="healthy", errors=0, warnings=0, information=0)
    )


@patch("domains.analysis.api.orchestrator.aggregator.analyze")
def test_api_full_analysis_success(mock_analyze):
    """POST /api/v1/analysis returns protocol-centric configuration states."""
    mock_analyze.return_value = make_healthy_aggregated_response()

    response = client.post("/api/v1/analysis", json={"domain": "example.com", "selector": "s1"})
    assert response.status_code == 200

    data = response.json()
    # Core domain field
    assert data["domain"] == "example.com"
    assert "score" not in data
    assert data["protocols"]["spf"]["status"] == "CONFIGURED"
    assert data["protocols"]["dkim"]["status"] == "CONFIGURED"
    assert data["protocols"]["dmarc"]["status"] == "CONFIGURED"
    assert "recommendations" in data


def test_header_analysis_endpoint():
    headers = "From: sender@example.com\nAuthentication-Results: mx.test; spf=pass smtp.mailfrom=bounce.example.com; dkim=pass header.d=sendgrid.net; dmarc=fail\n"
    response = client.post("/api/v1/analysis/headers", json={"headers": headers})
    assert response.status_code == 200
    assert response.json()["root_cause"]["title"] == "DKIM Alignment Failure"


@patch("domains.analysis.api.orchestrator.orchestrate_combined_diagnostic")
def test_combined_endpoint_returns_configuration_and_message_evidence(mock_combined):
    from domains.analysis.schemas import ProtocolConfiguration, UnifiedDiagnosticResponse
    mock_combined.return_value = UnifiedDiagnosticResponse(configuration={"spf": ProtocolConfiguration(status="CONFIGURED"), "dkim": ProtocolConfiguration(status="UNKNOWN"), "dmarc": ProtocolConfiguration(status="CONFIGURED")}, message_analysis={"spf": "PASS", "dkim": "FAIL", "dmarc": "FAIL"}, root_cause={"title": "DKIM Alignment Failure", "description": "Not aligned"}, remediation=[{"step": 1, "action": "Configure custom DKIM signing domain."}])
    response = client.post("/api/v1/analysis/combined", json={"domain": "example.com", "headers": "From: sender@example.com"})
    assert response.status_code == 200
    assert response.json()["message_analysis"]["dkim"] == "FAIL"
