from fastapi import APIRouter, HTTPException
from domains.analysis.dns.resolver import DNSResolver
from domains.analysis.validators.spf import SPFValidator
from domains.analysis.validators.dkim import DKIMValidator
from domains.analysis.validators.dmarc import DMARCValidator
from domains.analysis.services.dkim_discovery import DKIMDiscoveryService
from domains.analysis.aggregator.aggregator import AnalysisAggregator
from shared.models import FullAnalysisRequest
from core.orchestrator import IntelligenceOrchestrator
from domains.analysis.schemas import DomainDiagnosticResponse, UnifiedDiagnosticResponse
from domains.header_analysis.header_parser import HeaderParser
from domains.header_analysis.schemas import HeaderAnalysisResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/analysis", tags=["analysis"])
dns_resolver = DNSResolver()
spf_validator = SPFValidator(dns_resolver)
dkim_validator = DKIMValidator(dns_resolver)
dmarc_validator = DMARCValidator(dns_resolver)
dkim_discovery_service = DKIMDiscoveryService()

aggregator_service = AnalysisAggregator(dns_resolver, spf_validator, dkim_validator, dmarc_validator, dkim_discovery_service)
orchestrator = IntelligenceOrchestrator(aggregator_service)

@router.post("")
@router.post("/")
def run_full_analysis(request: FullAnalysisRequest):
    """
    Run full authentication triangulation (DNS, SPF, DKIM, DMARC) through the
    IntelligenceOrchestrator. The analysis domain has no direct dependency on the
    rules domain — all cross-domain coordination is handled by the orchestrator
    per ARCH-014.
    """
    if not dns_resolver.validate_domain(request.domain):
        raise HTTPException(status_code=400, detail="Invalid domain format")

    return orchestrator.orchestrate_domain_diagnostic(request.domain, request.selector)


class HeaderAnalysisRequest(BaseModel):
    headers: str = Field(min_length=1, max_length=100_000)


@router.post("/headers", response_model=HeaderAnalysisResponse)
def analyze_headers(request: HeaderAnalysisRequest):
    return HeaderParser().parse(request.headers)


class CombinedAnalysisRequest(HeaderAnalysisRequest):
    domain: str
    selector: str | None = None


@router.post("/combined", response_model=UnifiedDiagnosticResponse)
def analyze_combined(request: CombinedAnalysisRequest):
    if not dns_resolver.validate_domain(request.domain):
        raise HTTPException(status_code=400, detail="Invalid domain format")
    return orchestrator.orchestrate_combined_diagnostic(request.domain, request.headers, request.selector)
