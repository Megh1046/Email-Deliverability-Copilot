import pytest
from unittest.mock import MagicMock
from domains.analysis.aggregator.aggregator import AnalysisAggregator
from domains.analysis.dns.resolver import DNSResolver
from domains.analysis.validators.spf import SPFValidator
from domains.analysis.validators.dkim import DKIMValidator
from domains.analysis.validators.dmarc import DMARCValidator
from domains.analysis.shared.models import AnalysisIssue
from domains.analysis.schemas import SpfResult, DkimResult, DmarcResult, DnsAnalysisResponse, DmarcAlignment, DmarcReporting

@pytest.fixture
def aggregator():
    resolver = MagicMock(spec=DNSResolver)
    resolver.lookup_all.return_value = {"MX": []}
    resolver.to_response.return_value = DnsAnalysisResponse(domain="example.com", lookupStatus="success", lookupTimeMs=10, records={}, errors=[])
    
    spf = MagicMock(spec=SPFValidator)
    dkim = MagicMock(spec=DKIMValidator)
    dmarc = MagicMock(spec=DMARCValidator)
    
    return AnalysisAggregator(resolver, spf, dkim, dmarc)

def test_aggregator_healthy(aggregator):
    aggregator.spf.analyze.return_value = SpfResult(exists=True, record="v=spf1 ~all", syntaxValid=True, lookupCount=0, issues=[], warnings=[])
    aggregator.dkim.analyze.return_value = DkimResult(exists=True, selector="s1", record="v=DKIM1", syntaxValid=True, keyType="rsa", issues=[], warnings=[])
    aggregator.dmarc.analyze.return_value = DmarcResult(
        exists=True, record="v=DMARC1; p=reject;", syntaxValid=True, policy="reject", subdomainPolicy="reject", percentage=100, 
        alignment=DmarcAlignment(dkim="r", spf="r"), reporting=DmarcReporting(), issues=[], warnings=[]
    )
    
    response = aggregator.analyze("example.com", "s1")
    assert response.summary.errors == 0
    assert response.summary.warnings == 0
    assert response.summary.status == "healthy"

def test_aggregator_no_selector_is_unknown_not_critical(aggregator):
    aggregator.spf.analyze.return_value = SpfResult(exists=True, record="v=spf1 ~all", syntaxValid=True, lookupCount=0, issues=[], warnings=[])
    aggregator.dmarc.analyze.return_value = DmarcResult(
        exists=True, record="v=DMARC1; p=reject;", syntaxValid=True, policy="reject", subdomainPolicy="reject", percentage=100, 
        alignment=DmarcAlignment(dkim="r", spf="r"), reporting=DmarcReporting(), issues=[], warnings=[]
    )
    aggregator.dkim.analyze.return_value = DkimResult(
        exists=False, selector="", record="", syntaxValid=False, keyType="",
        issues=[AnalysisIssue(code="MISSING_DKIM", severity="error", message="No DKIM record found.")]
    )
    
    # A domain cannot enumerate its DKIM selectors, so this is not a failure.
    response = aggregator.analyze("example.com")
    assert response.summary.errors == 0
    assert response.dkim.status == "UNKNOWN"

def test_aggregator_warnings_only(aggregator):
    aggregator.spf.analyze.return_value = SpfResult(exists=True, record="v=spf1 ~all", syntaxValid=True, lookupCount=0, issues=[], warnings=[AnalysisIssue(code="WARN", severity="warning", message="")])
    aggregator.dkim.analyze.return_value = DkimResult(exists=True, selector="s1", record="v=DKIM1", syntaxValid=True, keyType="rsa", issues=[], warnings=[])
    aggregator.dmarc.analyze.return_value = DmarcResult(
        exists=True, record="v=DMARC1; p=reject;", syntaxValid=True, policy="reject", subdomainPolicy="reject", percentage=100, 
        alignment=DmarcAlignment(dkim="r", spf="r"), reporting=DmarcReporting(), issues=[], warnings=[]
    )
    
    response = aggregator.analyze("example.com", "s1")
    assert response.summary.errors == 0
    assert response.summary.warnings == 1
    assert response.summary.status == "warning"
