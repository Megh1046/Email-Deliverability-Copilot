import pytest
from unittest.mock import patch, MagicMock
from domains.analysis.validators.dmarc import DMARCValidator
from domains.analysis.dns.resolver import DNSResolver

@pytest.fixture
def dmarc_validator():
    resolver = DNSResolver()
    return DMARCValidator(resolver)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dmarc_missing(mock_lookup, dmarc_validator):
    mock_lookup.return_value = (["some random text"], None)
    result = dmarc_validator.analyze("example.com")
    
    assert not result.exists
    assert len(result.issues) == 1
    assert result.issues[0].code == "MISSING_DMARC"

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dmarc_valid(mock_lookup, dmarc_validator):
    mock_lookup.return_value = (["v=DMARC1; p=reject; rua=mailto:a@b.com, mailto:c@d.com; adkim=s;"], None)
    result = dmarc_validator.analyze("example.com")
    
    assert result.exists
    assert result.syntaxValid
    assert result.policy == "reject"
    assert result.subdomainPolicy == "reject"
    assert result.alignment.dkim == "s"
    assert result.alignment.spf == "r"
    assert result.percentage == 100
    assert len(result.reporting.rua) == 2
    assert not result.issues

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dmarc_invalid_policy(mock_lookup, dmarc_validator):
    mock_lookup.return_value = (["v=DMARC1; p=drop; pct=notanumber"], None)
    result = dmarc_validator.analyze("example.com")
    
    assert result.exists
    assert any(i.code == "INVALID_POLICY" for i in result.issues)
    assert any(i.code == "INVALID_PERCENTAGE" for i in result.issues)
    assert result.percentage == 100

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dmarc_missing_mandatory(mock_lookup, dmarc_validator):
    mock_lookup.return_value = (["v=DMARC1; sp=reject; rua=mailto:test@test.com"], None)
    result = dmarc_validator.analyze("example.com")
    
    assert result.exists
    assert any(i.code == "MISSING_POLICY" for i in result.issues)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dmarc_duplicate_and_unknown(mock_lookup, dmarc_validator):
    mock_lookup.return_value = (["v=DMARC1; p=none; p=reject; unknown=1"], None)
    result = dmarc_validator.analyze("example.com")
    
    assert result.exists
    assert not result.syntaxValid
    assert any(i.code == "DUPLICATE_TAG" for i in result.issues)
    assert any(i.code == "UNKNOWN_TAG" for i in result.warnings)
