import pytest
from domains.rules.engine import RuleEngine
from domains.rules.score_calculator import ScoreCalculator
from domains.rules.recommendation_mapper import RecommendationMapper
from domains.rules.business_translator import BusinessTranslator
from domains.analysis.aggregator.schemas import AggregatedAnalysisResponse, AnalysisSummary
from domains.analysis.schemas import SpfResult, DkimResult, DmarcResult, DnsAnalysisResponse
from domains.analysis.shared.models import AnalysisIssue

@pytest.fixture
def rule_engine():
    score_calculator = ScoreCalculator()
    recommendation_mapper = RecommendationMapper()
    business_translator = BusinessTranslator()
    return RuleEngine(score_calculator, recommendation_mapper, business_translator)

def get_base_response():
    return AggregatedAnalysisResponse(
        analysisId="test",
        domain="example.com",
        status="completed",
        timestamp="2026-07-29T10:00:00Z",
        dns=DnsAnalysisResponse(domain="example.com", lookupStatus="success", lookupTimeMs=10, records={}),
        spf=SpfResult(exists=False, record="", syntaxValid=False, lookupCount=0, mechanisms=[], include_domains=[], ip4_ranges=[], issues=[], warnings=[]),
        dkim=DkimResult(exists=False, selector="", record="", syntaxValid=False, keyType="", issues=[], warnings=[], tags={}),
        dmarc=DmarcResult(exists=False, record="", policy="", subdomainPolicy="", percentage=100, alignment={"dkim": "r", "spf": "r"}, reporting={"rua": [], "ruf": []}, syntaxValid=False, issues=[], warnings=[], tags={}),
        summary=AnalysisSummary(status="completed", errors=0, warnings=0, information=0)
    )

def test_no_authentication_present(rule_engine):
    response = get_base_response()
    response.spf.issues = [AnalysisIssue(code="MISSING_SPF", severity="error", message="missing")]
    response.dkim.issues = [AnalysisIssue(code="MISSING_DKIM", severity="error", message="missing")]
    response.dmarc.issues = [AnalysisIssue(code="MISSING_DMARC", severity="error", message="missing")]
    
    result = rule_engine.evaluate(response)
    
    assert "XPRO-001" in [i.insight_id for i in result.active_insights]
    # Double counting prevention: SPF-001, DKIM-001, DMARC-001 (-20 each) are suppressed by XPRO-001.
    # Raw: 100 - 20 (XPRO-001) = 80. However, XPRO-001 is CRITICAL.
    # ARCH-015 severity ceiling: CRITICAL → score capped at 49.
    assert result.score.score == 49
    assert result.score.band == "POOR"

def test_fully_healthy_domain(rule_engine):
    response = get_base_response()
    response.spf.exists = True
    response.dkim.exists = True
    response.dmarc.exists = True
    response.dmarc.record = "v=DMARC1; p=reject;"
    
    result = rule_engine.evaluate(response)
    
    assert "XPRO-012" in [i.insight_id for i in result.active_insights]
    assert "DMARC-017" in [i.insight_id for i in result.active_insights]
    assert result.score.score == 100 # Base 100 + bonuses => clamped to 100

def test_spf_only(rule_engine):
    response = get_base_response()
    response.spf.exists = True
    response.dmarc.exists = True
    response.dkim.issues = [AnalysisIssue(code="MISSING_DKIM", severity="error", message="missing")]
    response.dmarc.issues = [AnalysisIssue(code="P_NONE", severity="warning", message="p=none")]
    
    result = rule_engine.evaluate(response)
    ids = [i.insight_id for i in result.active_insights]
    assert "SPF-001" not in ids
    assert "DKIM-001" in ids
    assert "DMARC-005" in ids
    
    # DKIM-001 is CRITICAL (weight -20) and DMARC-005 is HIGH (weight -15).
    # Raw: 100 - 20 - 15 = 65. However, DKIM-001 is CRITICAL.
    # ARCH-015 severity ceiling: CRITICAL → score capped at 49.
    assert result.score.score == 49
    assert result.score.band == "POOR"
    
def test_boundaries(rule_engine):
    response = get_base_response()
    response.spf.issues = [
        AnalysisIssue(code="MISSING_SPF", severity="error", message=""),
        AnalysisIssue(code="MULTIPLE_RECORDS", severity="error", message=""),
        AnalysisIssue(code="ENDS_WITH_PLUS_ALL", severity="error", message=""),
        AnalysisIssue(code="LIMIT_EXCEEDED", severity="error", message="")
    ] 
    response.dkim.issues = [AnalysisIssue(code="MISSING_DKIM", severity="error", message="missing")] 
    response.dmarc.issues = [AnalysisIssue(code="MISSING_DMARC", severity="error", message="missing")] 
    
    result = rule_engine.evaluate(response)
    # 100 - 20 (XPRO-001) - 20 (SPF-002) - 20 (SPF-005) - 12 (SPF-008) = 28
    assert result.score.score == 28
    assert result.score.band == "POOR"

def test_recommendation_ranking(rule_engine):
    response = get_base_response()
    response.spf.issues = [AnalysisIssue(code="MISSING_SPF", severity="error", message="")]
    response.dkim.issues = [AnalysisIssue(code="MISSING_DKIM", severity="error", message="")]
    response.dmarc.issues = [AnalysisIssue(code="MISSING_DMARC", severity="error", message="")]
    
    result = rule_engine.evaluate(response)
    
    assert len(result.recommendations) > 0
    # XPRO-001 recommendation should be top priority
    p1_recommendations = [r.insight_id for r in result.recommendations if r.priority_rank == "P1"]
    assert "XPRO-001" in p1_recommendations
