from unittest.mock import MagicMock

from domains.analysis.aggregator.aggregator import AnalysisAggregator
from domains.analysis.dns.resolver import DNSResolver
from domains.analysis.schemas import DkimResult, DmarcAlignment, DmarcReporting, DmarcResult, DnsAnalysisResponse, SpfResult
from domains.analysis.services.dkim_discovery import DKIMDiscoveryService
from domains.analysis.validators.dkim import DKIMValidator
from domains.analysis.validators.dmarc import DMARCValidator
from domains.analysis.validators.spf import SPFValidator


def _aggregator():
    resolver = MagicMock(spec=DNSResolver)
    resolver.lookup_all.return_value = {"records": {"mx": ["10 aspmx.l.google.com"]}, "errors": []}
    resolver.to_response.return_value = DnsAnalysisResponse(domain="example.com", lookupStatus="success", lookupTimeMs=0, records={})
    spf = MagicMock(spec=SPFValidator)
    spf.analyze.return_value = SpfResult(exists=True, record="v=spf1 include:_spf.google.com ~all", syntaxValid=True, lookupCount=1, mechanisms=["include:_spf.google.com"])
    dkim = MagicMock(spec=DKIMValidator)
    dmarc = MagicMock(spec=DMARCValidator)
    dmarc.analyze.return_value = DmarcResult(exists=True, record="v=DMARC1; p=reject", syntaxValid=True, policy="reject", subdomainPolicy="reject", percentage=100, alignment=DmarcAlignment(dkim="r", spf="r"), reporting=DmarcReporting())
    return AnalysisAggregator(resolver, spf, dkim, dmarc, DKIMDiscoveryService())


def test_domain_only_dkim_is_unknown_and_does_not_probe_guesses():
    aggregator = _aggregator()
    response = aggregator.analyze("example.com")
    assert aggregator.dkim.analyze.call_count == 0
    assert response.dkim.status == "UNKNOWN"
    assert response.dkim.provider == "Google Workspace"


def test_explicit_selector_is_checked_once():
    aggregator = _aggregator()
    aggregator.dkim.analyze.return_value = DkimResult(exists=True, selector="google", record="v=DKIM1; p=abc", syntaxValid=True, keyType="rsa", status="VERIFIED")
    response = aggregator.analyze("example.com", "google")
    aggregator.dkim.analyze.assert_called_once_with("example.com", "google")
    assert response.dkim.exists
