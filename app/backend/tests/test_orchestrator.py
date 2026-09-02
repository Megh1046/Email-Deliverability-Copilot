"""
Tests for IntelligenceOrchestrator (M2F)

Validates that the orchestrator correctly:
- Passes aggregator output into the rule engine
- Returns a RuleEngineResponse
- Propagates the domain and selector correctly
- Leaves RuleEngineResponse contract unchanged
"""
import pytest
from unittest.mock import MagicMock, patch
from core.orchestrator import IntelligenceOrchestrator
from domains.analysis.aggregator.schemas import AggregatedAnalysisResponse, AnalysisSummary
from domains.analysis.schemas import (
    DnsAnalysisResponse, SpfResult, DkimResult, DmarcResult,
    DmarcAlignment, DmarcReporting
)
from domains.rules.schemas import RuleEngineResponse, DeliverabilityScore


def make_mock_aggregated_response(domain: str = "example.com") -> AggregatedAnalysisResponse:
    return AggregatedAnalysisResponse(
        analysisId="test-id-123",
        domain=domain,
        status="completed",
        timestamp="2026-07-29T00:00:00Z",
        dns=DnsAnalysisResponse(
            domain=domain, lookupStatus="success",
            lookupTimeMs=10, records={}, errors=[]
        ),
        spf=SpfResult(
            exists=True, record="v=spf1 -all", syntaxValid=True,
            lookupCount=0, issues=[], warnings=[], mechanisms=[]
        ),
        dkim=DkimResult(
            exists=True, selector="s1", record="v=DKIM1; k=rsa; p=abc",
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


@pytest.fixture
def mock_aggregator():
    aggregator = MagicMock()
    aggregator.analyze.return_value = make_mock_aggregated_response()
    return aggregator


@pytest.fixture
def orchestrator(mock_aggregator):
    """Create orchestrator with mocked aggregator; RuleEngine runs for real."""
    return IntelligenceOrchestrator(mock_aggregator)


class TestIntelligenceOrchestrator:

    def test_orchestrator_returns_rule_engine_response(self, orchestrator):
        """Orchestrator must always return RuleEngineResponse."""
        result = orchestrator.orchestrate_analysis("example.com")
        assert isinstance(result, RuleEngineResponse)

    def test_orchestrator_passes_domain_to_aggregator(self, orchestrator, mock_aggregator):
        """Aggregator must be called with the correct domain."""
        orchestrator.orchestrate_analysis("testdomain.com", selector="s1")
        mock_aggregator.analyze.assert_called_once_with("testdomain.com", "s1")

    def test_orchestrator_passes_selector_to_aggregator(self, orchestrator, mock_aggregator):
        """Selector argument is forwarded correctly to the aggregator."""
        orchestrator.orchestrate_analysis("example.com", selector="google")
        call_args = mock_aggregator.analyze.call_args
        assert call_args[0][1] == "google"

    def test_orchestrator_selector_defaults_to_none(self, orchestrator, mock_aggregator):
        """When no selector is provided, aggregator receives None."""
        orchestrator.orchestrate_analysis("example.com")
        mock_aggregator.analyze.assert_called_once_with("example.com", None)

    def test_response_contains_required_base_fields(self, orchestrator):
        """RuleEngineResponse must include BaseApiResponse fields."""
        result = orchestrator.orchestrate_analysis("example.com")
        assert hasattr(result, "version")
        assert hasattr(result, "timestamp")
        assert hasattr(result, "requestId")
        assert result.version == "1.0"
        assert result.timestamp is not None
        assert result.requestId is not None

    def test_response_contains_domain(self, orchestrator):
        """RuleEngineResponse must carry the domain field."""
        result = orchestrator.orchestrate_analysis("example.com")
        assert result.domain == "example.com"

    def test_response_contains_score(self, orchestrator):
        """RuleEngineResponse must contain a deliverability score."""
        result = orchestrator.orchestrate_analysis("example.com")
        assert hasattr(result, "score")
        assert isinstance(result.score, DeliverabilityScore)

    def test_response_contains_recommendations(self, orchestrator):
        """RuleEngineResponse must contain a recommendations list."""
        result = orchestrator.orchestrate_analysis("example.com")
        assert hasattr(result, "recommendations")
        assert isinstance(result.recommendations, list)

    def test_aggregator_called_exactly_once(self, orchestrator, mock_aggregator):
        """Aggregator.analyze must be called exactly once per orchestration."""
        orchestrator.orchestrate_analysis("example.com")
        assert mock_aggregator.analyze.call_count == 1

    def test_aggregator_failure_propagates(self, mock_aggregator):
        """Exceptions from aggregator must propagate out of the orchestrator."""
        mock_aggregator.analyze.side_effect = RuntimeError("DNS timeout")
        orch = IntelligenceOrchestrator(mock_aggregator)
        with pytest.raises(RuntimeError, match="DNS timeout"):
            orch.orchestrate_analysis("broken.com")
