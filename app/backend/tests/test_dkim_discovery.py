import pytest

from domains.analysis.schemas import SpfResult
from domains.analysis.services.dkim_discovery import DKIMDiscoveryService


@pytest.fixture
def discovery_service():
    return DKIMDiscoveryService()


def test_provider_fingerprint_reads_lowercase_resolver_key(discovery_service):
    spf = SpfResult(exists=True, record="v=spf1 include:_spf.google.com ~all", syntaxValid=True, lookupCount=1, mechanisms=["include:_spf.google.com"])
    selectors, provider = discovery_service.discover_selectors("example.com", {"mx": ["1 aspmx.l.google.com"]}, spf)
    assert provider == "Google Workspace"
    assert selectors == []


def test_explicit_selector_is_the_only_selector_checked(discovery_service):
    spf = SpfResult(exists=False, record="", syntaxValid=False, lookupCount=0)
    selectors, provider = discovery_service.discover_selectors("example.com", {"mx": []}, spf, "customer-2026")
    assert provider is None
    assert selectors == ["customer-2026"]
