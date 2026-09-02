import pytest
from unittest.mock import patch, MagicMock
from domains.analysis.dns.resolver import DNSResolver
import dns.resolver

@pytest.fixture
def dns_service():
    return DNSResolver()

class MockRData:
    def __init__(self, val, rtype):
        self._val = val
        self.rtype = rtype
        
        class MockName:
            def __init__(self, name):
                self.name = name
            def to_text(self, omit_final_dot=False):
                return self.name

        if rtype == "MX":
            self.preference = 10
            self.exchange = MockName(val)
        elif rtype == "SOA":
            parts = val.split()
            self.mname = MockName(parts[0])
            self.rname = MockName(parts[1])
            self.serial = int(parts[2])
            self.refresh = int(parts[3])
            self.retry = int(parts[4])
            self.expire = int(parts[5])
            self.minimum = int(parts[6])

    def to_text(self, omit_final_dot=False):
        return self._val

def test_validate_domain(dns_service):
    assert dns_service.validate_domain("example.com") is True
    assert dns_service.validate_domain("invalid domain") is False
    assert dns_service.validate_domain("") is False

@patch("dns.resolver.Resolver.resolve")
def test_lookup_success(mock_resolve, dns_service):
    def side_effect(domain, rtype):
        if rtype == "A":
            return [MockRData("127.0.0.1", "A")]
        elif rtype == "MX":
            return [MockRData("mail.example.com", "MX")]
        elif rtype == "TXT" and not domain.startswith("_dmarc"):
            return [MockRData("\"v=spf1 -all\"", "TXT")]
        elif rtype == "SOA":
            return [MockRData("ns1.test.com admin.test.com 1 2 3 4 5", "SOA")]
        else:
            raise dns.resolver.NoAnswer()
            
    mock_resolve.side_effect = side_effect
    
    result = dns_service.lookup_all("example.com")
    
    assert result["records"]["a"] == ["127.0.0.1"]
    assert result["records"]["mx"] == ["10 mail.example.com"]
    assert result["records"]["txt"] == ["v=spf1 -all"]
    assert result["records"]["soa"] == ["ns1.test.com admin.test.com 1 2 3 4 5"]
    assert result["records"]["ns"] == []
    assert len(result["errors"]) == 0

@patch("dns.resolver.Resolver.resolve")
def test_lookup_nxdomain(mock_resolve, dns_service):
    mock_resolve.side_effect = dns.resolver.NXDOMAIN()
    
    result = dns_service.lookup_all("nonexistent.com")
    
    # All records should have a Domain does not exist error
    assert len(result["errors"]) > 0
    assert result["errors"][0]["message"] == "Domain does not exist"

@patch("dns.resolver.Resolver.resolve")
def test_lookup_timeout(mock_resolve, dns_service):
    mock_resolve.side_effect = dns.resolver.Timeout()
    
    result = dns_service.lookup_all("timeout.com")
    assert len(result["errors"]) > 0
    assert result["errors"][0]["message"] == "Timeout"

@patch("domains.analysis.dns.resolver.time.sleep")
@patch("dns.resolver.Resolver.resolve")
def test_timeout_retries_twice_with_required_backoff(mock_resolve, mock_sleep, dns_service):
    mock_resolve.side_effect = dns.resolver.Timeout()
    _, error = dns_service.lookup_record("TXT", "timeout.example")
    assert error == "Timeout"
    assert mock_resolve.call_count == 3
    assert [call.args[0] for call in mock_sleep.call_args_list] == [0.15, 0.3]

@patch("dns.resolver.Resolver.resolve")
def test_no_answer_is_not_retried(mock_resolve, dns_service):
    mock_resolve.side_effect = dns.resolver.NoAnswer()
    records, error = dns_service.lookup_record("TXT", "empty.example")
    assert records == []
    assert error is None
    assert mock_resolve.call_count == 1

@patch("dns.resolver.Resolver.resolve")
def test_lookup_partial_failure(mock_resolve, dns_service):
    def side_effect(domain, rtype):
        if rtype == "A":
            return [MockRData("127.0.0.1", "A")]
        else:
            raise Exception("Resolver failure")
            
    mock_resolve.side_effect = side_effect
    
    result = dns_service.lookup_all("partial.com")
    assert result["records"]["a"] == ["127.0.0.1"]
    assert len(result["errors"]) > 0
    assert any(err["message"] == "Resolver failure" for err in result["errors"])
