from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from shared.models import AnalysisIssue, DomainRequest

class DnsError(BaseModel):
    record: str
    message: str

class DnsAnalysisResponse(BaseModel):
    domain: str
    lookupStatus: str
    lookupTimeMs: int
    records: Dict[str, List[str]]
    errors: List[DnsError] = []

class SpfResult(BaseModel):
    exists: bool
    record: str
    syntaxValid: bool
    lookupCount: int
    issues: List[AnalysisIssue] = []
    warnings: List[AnalysisIssue] = []
    mechanisms: List[str] = []

class DkimResult(BaseModel):
    exists: bool
    selector: str
    record: str
    syntaxValid: bool
    keyType: str
    keyLength: Optional[int] = None
    provider: Optional[str] = None
    # VERIFIED, MISSING, INVALID, UNKNOWN, or ERROR.  UNKNOWN is not a fail.
    status: str = "UNKNOWN"
    issues: List[AnalysisIssue] = []
    warnings: List[AnalysisIssue] = []
    tags: Dict[str, str] = {}

class DmarcAlignment(BaseModel):
    dkim: str
    spf: str

class DmarcReporting(BaseModel):
    rua: List[str] = []
    ruf: List[str] = []

class DmarcResult(BaseModel):
    exists: bool
    record: str
    syntaxValid: bool
    policy: str
    subdomainPolicy: str
    percentage: int
    alignment: DmarcAlignment
    reporting: DmarcReporting
    issues: List[AnalysisIssue] = []
    warnings: List[AnalysisIssue] = []
    tags: Dict[str, str] = {}

class DnsVerificationResult(BaseModel):
    analysisId: str
    domain: str
    status: str
    timestamp: str
    dns: DnsAnalysisResponse
    spf: SpfResult
    dkim: DkimResult
    dmarc: DmarcResult
