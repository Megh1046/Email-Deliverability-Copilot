import pytest
import base64
from unittest.mock import patch, MagicMock
from domains.analysis.validators.dkim import DKIMValidator
from domains.analysis.dns.resolver import DNSResolver

@pytest.fixture
def dkim_validator():
    resolver = DNSResolver()
    return DKIMValidator(resolver)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dkim_rejects_unrelated_txt_record(mock_lookup, dkim_validator):
    mock_lookup.return_value = (["some text"], None)
    result = dkim_validator.analyze("example.com", "default")
    
    assert not result.exists
    assert len(result.issues) == 1
    assert result.issues[0].code == "INVALID_DKIM_RECORD"
    assert result.selector == "default"

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dkim_rejects_spf_txt_record(mock_lookup, dkim_validator):
    mock_lookup.return_value = (["v=spf1 ~all"], None)
    result = dkim_validator.analyze("hubspot.com", "default")
    assert not result.exists
    assert result.status == "INVALID"
    assert result.issues[0].code == "INVALID_DKIM_RECORD"

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dkim_valid(mock_lookup, dkim_validator):
    # A standard mock 2048 bit public key (represented as fake b64 bytes of len 256)
    mock_key = base64.b64encode(b"0" * 256).decode("utf-8")
    mock_lookup.return_value = ([f"v=DKIM1; k=rsa; p={mock_key}"], None)
    result = dkim_validator.analyze("example.com", "google")
    
    assert result.exists
    assert result.syntaxValid
    assert result.keyType == "rsa"
    # base64 decodes back to 256 bytes * 8 = 2048 bits
    assert result.keyLength == 2048
    assert not result.issues
    assert result.tags["v"] == "DKIM1"
    assert result.tags["p"] == mock_key

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dkim_invalid_version(mock_lookup, dkim_validator):
    mock_key = base64.b64encode(b"0" * 256).decode("utf-8")
    # Record validly starts with v=DKIM1; but we mistakenly append another v= or just malform it... 
    # Wait, the validation logic strictly looks for v= tag inside the dict
    mock_lookup.return_value = ([f"v=DKIM1; k=rsa; p={mock_key}; v=DKIM2;"], None)
    result = dkim_validator.analyze("example.com", "s1")
    
    assert result.exists
    # It will also have DUPLICATE_TAG and INVALID_VERSION since v is duplicated and last wins or is duplicate
    # Actually, in dict the first or last might win (here missing versions override if it breaks)
    assert any(i.code == "DUPLICATE_TAG" for i in result.issues)
    assert not result.syntaxValid

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dkim_missing_public_key(mock_lookup, dkim_validator):
    mock_lookup.return_value = (["v=DKIM1; k=rsa;"], None)
    result = dkim_validator.analyze("example.com", "default")
    
    assert result.exists
    assert any(i.code == "MISSING_KEY" for i in result.issues)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dkim_unsupported_key(mock_lookup, dkim_validator):
    mock_key = base64.b64encode(b"0" * 256).decode("utf-8")
    mock_lookup.return_value = ([f"v=DKIM1; k=dsa; p={mock_key}"], None)
    result = dkim_validator.analyze("example.com", "default")
    
    assert result.exists
    assert any(i.code == "UNSUPPORTED_KEY" for i in result.issues)

@patch("domains.analysis.dns.resolver.DNSResolver.lookup_record")
def test_dkim_malformed_tag_and_unknown(mock_lookup, dkim_validator):
    mock_key = base64.b64encode(b"0" * 256).decode("utf-8")
    mock_lookup.return_value = ([f"v=DKIM1; k=rsa; p={mock_key}; x; z=123"], None)
    result = dkim_validator.analyze("example.com", "default")
    
    assert result.exists
    assert not result.syntaxValid
    assert any(i.code == "INVALID_SYNTAX" for i in result.issues) # for the "x"
    assert any(i.code == "UNKNOWN_TAG" for i in result.warnings) # for the "z"
