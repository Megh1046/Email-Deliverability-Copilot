from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# New Header Analysis architecture
from domains.header_analysis.pipeline import HeaderAnalysisPipeline
from domains.header_analysis.schemas import HeaderAnalysisResponse
from domains.dns.dns_verifier import DnsVerifier
from domains.dns.resolver import DNSResolver
from domains.dns.spf_verifier import SPFValidator
from domains.dns.dkim_verifier import DKIMValidator
from domains.dns.dmarc_verifier import DMARCValidator
from domains.dns.provider_detector import DKIMDiscoveryService
from domains.dns.schemas import DnsVerificationResult

router = APIRouter(prefix="/analysis", tags=["analysis"])

# ── New Header Analysis Pipeline Initialization ───────────────
header_pipeline = HeaderAnalysisPipeline()

# ── DNS Verifier Initialization ───────────────
dns_resolver = DNSResolver()
spf_validator = SPFValidator(dns_resolver)
dkim_validator = DKIMValidator(dns_resolver)
dmarc_validator = DMARCValidator(dns_resolver)
dkim_discovery_service = DKIMDiscoveryService()
dns_verifier = DnsVerifier(dns_resolver, spf_validator, dkim_validator, dmarc_validator, dkim_discovery_service)

# ---------------------------------------------------------------------------
# Primary Endpoint
# ---------------------------------------------------------------------------

class HeaderAnalysisRequest(BaseModel):
    headers: str = Field(min_length=1, max_length=100_000)
    provider_hint: str | None = None
    spf_alignment_mode: str = "relaxed"
    dkim_alignment_mode: str = "relaxed"

@router.post("/headers", response_model=HeaderAnalysisResponse)
def analyze_headers(request: HeaderAnalysisRequest):
    """
    Primary troubleshooting endpoint.
    Parses raw email headers, diagnoses authentication failures,
    and returns step-by-step remediation.
    """
    return header_pipeline.analyze(
        raw_headers=request.headers,
        provider_hint=request.provider_hint,
        spf_alignment_mode=request.spf_alignment_mode,
        dkim_alignment_mode=request.dkim_alignment_mode,
    )

# ---------------------------------------------------------------------------
# Verification Endpoint
# ---------------------------------------------------------------------------

class VerifyRemediationRequest(BaseModel):
    domain: str
    selector: str | None = None

@router.post("/headers/verify", response_model=DnsVerificationResult)
def verify_remediation(request: VerifyRemediationRequest):
    """
    Verification endpoint.
    Checks the current DNS records to verify if the recommended remediation was successfully applied.
    """
    if not dns_resolver.validate_domain(request.domain):
        raise HTTPException(status_code=400, detail="Invalid domain format")
    
    return dns_verifier.analyze(request.domain, request.selector)
