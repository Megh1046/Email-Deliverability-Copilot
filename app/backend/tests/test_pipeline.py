from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from domains.analysis.api import router
from domains.analysis.schemas import DiagnosticRecommendation, DomainDiagnosticResponse, ProtocolConfiguration

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@patch("domains.analysis.api.orchestrator.orchestrate_domain_diagnostic")
def test_domain_endpoint_never_exposes_a_delivery_score(mock_diagnostic):
    mock_diagnostic.return_value = DomainDiagnosticResponse(
        domain="example.com",
        protocols={
            "spf": ProtocolConfiguration(status="CONFIGURED"),
            "dkim": ProtocolConfiguration(status="UNKNOWN", reason="Selector not supplied"),
            "dmarc": ProtocolConfiguration(status="CONFIGURED"),
        },
        recommendations=[DiagnosticRecommendation(category="Verification", message="Provide a DKIM selector or upload email headers to verify DKIM authentication.")],
    )
    response = client.post("/analysis", json={"domain": "example.com"})
    assert response.status_code == 200
    data = response.json()
    assert "score" not in data
    assert data["protocols"]["dkim"]["status"] == "UNKNOWN"
    assert data["recommendations"]


def test_pipeline_invalid_domain():
    response = client.post("/analysis", json={"domain": "invalid_domain^"})
    assert response.status_code == 400
