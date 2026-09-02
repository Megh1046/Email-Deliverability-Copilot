import pytest
from unittest.mock import patch, MagicMock
from domains.analysis.validators.spf import SPFValidator
from domains.analysis.dns.resolver import DNSResolver

@pytest.fixture
def spf_validator():
    resolver = DNSResolver()
    return SPFValidator(resolver)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_spf_missing(mock_lookup, spf_validator):
    mock_lookup.return_value = (["some text"], None)
    result = spf_validator.analyze("example.com")
    
    assert not result.exists
    assert len(result.issues) == 1
    assert result.issues[0].code == "MISSING_SPF"

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_spf_multiple(mock_lookup, spf_validator):
    mock_lookup.return_value = (["v=spf1 -all", "v=spf1 include:foo -all"], None)
    result = spf_validator.analyze("example.com")
    
    assert result.exists
    assert any(i.code == "MULTIPLE_RECORDS" for i in result.issues)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_spf_valid(mock_lookup, spf_validator):
    mock_lookup.return_value = (["v=spf1 include:_spf.google.com ~all"], None)
    result = spf_validator.analyze("example.com")
    
    assert result.exists
    assert result.syntaxValid
    assert result.lookupCount == 1
    assert not result.issues
    assert not result.warnings
    assert result.mechanisms == ["v=spf1", "include:_spf.google.com", "~all"]

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_spf_invalid_syntax(mock_lookup, spf_validator):
    mock_lookup.return_value = (["v=spf1 includes:_spf.google.com ~all"], None)
    result = spf_validator.analyze("example.com")
    
    assert result.exists
    assert not result.syntaxValid
    assert any(i.code == "INVALID_SYNTAX" for i in result.issues)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_spf_exceeds_limits(mock_lookup, spf_validator):
    mock_lookup.return_value = (["v=spf1 a mx ptr exists:foo redirect=bar " + " ".join(["include:foo" for _ in range(6)]) + " ~all"], None)
    result = spf_validator.analyze("example.com")
    
    assert result.exists
    assert result.lookupCount == 11
    assert any(i.code == "LIMIT_EXCEEDED" for i in result.issues)
    assert any(w.code == "DEPRECATED_MECHANISM" for w in result.warnings)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_spf_missing_all(mock_lookup, spf_validator):
    mock_lookup.return_value = (["v=spf1 include:foo"], None)
    result = spf_validator.analyze("example.com")
    
    assert result.exists
    assert any(w.code == "MISSING_ALL" for w in result.warnings)
