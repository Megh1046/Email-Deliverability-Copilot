import dns.resolver
import threading
import time
from typing import Dict, Any, List, Tuple, Optional
from .schemas import DnsAnalysisResponse, DnsError

class DNSResolver:
    """DNS Intelligence Service for resolving multiple record types safely."""
    
    def __init__(self, retries: int = 2, timeout: float = 3.0, lifetime: float = 5.0):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = lifetime
        self.retries = retries
        self._cache: Dict[Tuple[str, str], Tuple[List[str], Optional[str]]] = {}
        self._cache_lock = threading.Lock()

    def validate_domain(self, domain: str) -> bool:
        """Validate domain format before lookup."""
        if not domain or not isinstance(domain, str):
            return False
        # simple validation, reject empty or things with spaces
        domain = domain.strip()
        if " " in domain or ".." in domain:
            return False
        if not "." in domain and domain != "localhost":
            return False
        return True

    def lookup_record(self, record_type: str, domain: str) -> Tuple[List[str], Optional[str]]:
        """Reusable DNS record lookup method."""
        key = (record_type.upper(), domain.lower().rstrip("."))
        with self._cache_lock:
            cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = self._lookup_with_retry(*key)
        with self._cache_lock:
            self._cache[key] = result
        return result

    def _lookup_with_retry(self, record_type: str, domain: str) -> Tuple[List[str], Optional[str]]:
        """Retry only transient resolver timeouts with bounded backoff."""
        for attempt in range(self.retries + 1):
            try:
                return self._resolve_once(record_type, domain)
            except dns.resolver.Timeout:
                if attempt == self.retries:
                    return [], "Timeout"
                time.sleep(0.15 * (2 ** attempt))
            except dns.resolver.NoAnswer:
                return [], None
            except dns.resolver.NXDOMAIN:
                return [], "Domain does not exist"
            except Exception as exc:
                return [], str(exc)
        return [], "Timeout"

    def _resolve_once(self, record_type: str, domain: str) -> Tuple[List[str], Optional[str]]:
        try:
            answers = self.resolver.resolve(domain, record_type)
            # Depending on record type, we format it as string
            results = []
            for rdata in answers:
                if record_type in ("MX",):
                    results.append(f"{rdata.preference} {rdata.exchange.to_text(omit_final_dot=True)}")
                elif record_type in ("TXT",):
                    strings = getattr(rdata, "strings", None)
                    if strings is None:
                        results.append(rdata.to_text().replace('"', ''))
                    else:
                        results.append("".join(
                            part.decode() if isinstance(part, bytes) else str(part)
                            for part in strings
                        ))
                elif record_type in ("SOA",):
                    results.append(f"{rdata.mname.to_text(omit_final_dot=True)} {rdata.rname.to_text(omit_final_dot=True)} {rdata.serial} {rdata.refresh} {rdata.retry} {rdata.expire} {rdata.minimum}")
                else:
                    results.append(rdata.to_text(omit_final_dot=True))
            return results, None
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
            raise

    def lookup_dmarc(self, domain: str) -> Tuple[List[str], Optional[str]]:
        """Retrieve _dmarc.<domain> TXT record."""
        dmarc_domain = f"_dmarc.{domain}"
        return self.lookup_record("TXT", dmarc_domain)

    def lookup_all(self, domain: str) -> Dict[str, Any]:
        """Execute all DNS lookups and return results & errors."""
        # A lookup_all call defines one analysis request. Keep the cache only
        # for the following validator calls so DNS changes are never held by
        # the process indefinitely.
        with self._cache_lock:
            self._cache.clear()
        record_types = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA"]
        records = {rt.lower(): [] for rt in record_types}
        records["dmarc"] = []
        errors = []

        # Validate domain first
        if not self.validate_domain(domain):
            errors.append({"record": "DOMAIN", "message": "Invalid domain format"})
            return {"records": records, "errors": errors}

        for rt in record_types:
            res, err = self.lookup_record(rt, domain)
            if err:
                errors.append({"record": rt, "message": err})
            records[rt.lower()] = res
            
        # DMARC
        dmarc_res, dmarc_err = self.lookup_dmarc(domain)
        if dmarc_err:
            errors.append({"record": "DMARC", "message": dmarc_err})
        records["dmarc"] = dmarc_res
        
        return {"records": records, "errors": errors}

    def to_response(self, domain: str, lookup_results: Dict[str, Any], elapsed_ms: int) -> DnsAnalysisResponse:
        """Convert lookup results into API response schema."""
        errors_models = [DnsError(**err) for err in lookup_results["errors"]]
        status = "success" if not any(err["message"] == "Domain does not exist" for err in lookup_results["errors"]) else "failed"
        
        return DnsAnalysisResponse(
            domain=domain,
            lookupStatus=status,
            lookupTimeMs=elapsed_ms,
            records=lookup_results["records"],
            errors=errors_models
        )
