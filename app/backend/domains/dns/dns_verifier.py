import uuid
from datetime import datetime, timezone
import time
from .schemas import DnsAnalysisResponse, SpfResult, DkimResult, DmarcResult, DnsVerificationResult
from .resolver import DNSResolver
from .spf_verifier import SPFValidator
from .dkim_verifier import DKIMValidator
from .dmarc_verifier import DMARCValidator
from shared.models import AnalysisIssue
from .provider_detector import DKIMDiscoveryService
from domains.shared.constants import UNKNOWN_SELECTOR

class DnsVerifier:
    def __init__(self, resolver: DNSResolver, spf: SPFValidator, dkim: DKIMValidator, dmarc: DMARCValidator, dkim_discovery: DKIMDiscoveryService = None):
        self.resolver = resolver
        self.spf = spf
        self.dkim = dkim
        self.dmarc = dmarc
        self.dkim_discovery = dkim_discovery or DKIMDiscoveryService()
        
    def analyze(self, domain: str, selector: str = None) -> DnsVerificationResult:
        analysis_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # 1. DNS execution
        start_time = time.time()
        dns_records = self.resolver.lookup_all(domain)
        dns_ms = int((time.time() - start_time) * 1000)
        dns_response = self.resolver.to_response(domain, dns_records, dns_ms)
        
        # 2. SPF execution
        spf_result = self.spf.analyze(domain)
        # 3. DKIM execution
        candidate_selectors, provider = self.dkim_discovery.discover_selectors(domain, dns_records, spf_result, selector)
        
        if candidate_selectors:
            dkim_result = self.dkim.analyze(domain, candidate_selectors[0])
        else:
            dkim_result = DkimResult(
                exists=False, selector="", record="", syntaxValid=False, keyType="", status="UNKNOWN",
                issues=[AnalysisIssue(code=UNKNOWN_SELECTOR, severity="info", message="DKIM cannot be determined because no selector was supplied.")],
                warnings=[], tags={}
            )
        
        dkim_result.provider = provider
            
        # 4. DMARC execution
        dmarc_result = self.dmarc.analyze(domain)
        
        # 5. Extract summaries
        errors = 0
        warnings = 0
        
        all_checks = [spf_result, dkim_result, dmarc_result]
        
        for check in all_checks:
            for issue in check.issues:
                if issue.severity == "error":
                    errors += 1
                elif issue.severity == "warning":
                    warnings += 1
            for warning in check.warnings:
                if warning.severity == "error":
                    errors += 1
                elif warning.severity == "warning":
                    warnings += 1
                    
        if errors > 0:
            status = "critical"
        elif warnings > 0:
            status = "warning"
        else:
            status = "healthy"
            
        return DnsVerificationResult(
            analysisId=analysis_id,
            domain=domain,
            status="completed",
            timestamp=timestamp,
            dns=dns_response,
            spf=spf_result,
            dkim=dkim_result,
            dmarc=dmarc_result
        )
