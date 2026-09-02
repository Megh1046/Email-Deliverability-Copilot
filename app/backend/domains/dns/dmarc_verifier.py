from typing import Dict, List, Tuple
from .resolver import DNSResolver
from .schemas import DmarcResult, DmarcAlignment, DmarcReporting
from shared.models import AnalysisIssue
from domains.shared.constants import DNS_ERROR, MISSING_DMARC, MULTIPLE_RECORDS

class DMARCValidator:
    """Intelligent DMARC record parser and validator."""

    def __init__(self, resolver: DNSResolver):
        self.resolver = resolver
    
    def analyze(self, domain: str) -> DmarcResult:
        dmarc_domain = f"_dmarc.{domain}"
        txt_records, err = self.resolver.lookup_record("TXT", dmarc_domain)
        
        if err:
            return DmarcResult(
                exists=False, record="", syntaxValid=False, policy="", subdomainPolicy="", percentage=100,
                alignment=DmarcAlignment(dkim="", spf=""), reporting=DmarcReporting(rua=[], ruf=[]),
                issues=[AnalysisIssue(code=DNS_ERROR, severity="error", message=err)],
                warnings=[], tags={}
            )
            
        dmarc_records = [r for r in txt_records if r.replace(" ", "").startswith("v=DMARC1")]
        
        if not dmarc_records:
            return DmarcResult(
                exists=False, record="", syntaxValid=False, policy="", subdomainPolicy="", percentage=100,
                alignment=DmarcAlignment(dkim="", spf=""), reporting=DmarcReporting(rua=[], ruf=[]),
                issues=[AnalysisIssue(code=MISSING_DMARC, severity="error", message="No DMARC record found.")],
                warnings=[], tags={}
            )
            
        issues = []
        warnings = []
        if len(dmarc_records) > 1:
            issues.append(AnalysisIssue(code=MULTIPLE_RECORDS, severity="error", message="Multiple DMARC records detected."))
            
        record = dmarc_records[0]
        tags, duplicates, syntax_errors, unknown_tags = self._parse_record(record)
        
        syntax_valid = len(syntax_errors) == 0 and len(duplicates) == 0
        for dup in duplicates:
            issues.append(AnalysisIssue(code="DUPLICATE_TAG", severity="error", message=f"Duplicate tag found: {dup}"))
        for stx in syntax_errors:
            issues.append(AnalysisIssue(code="INVALID_SYNTAX", severity="error", message=stx))
        for unk in unknown_tags:
            warnings.append(AnalysisIssue(code="UNKNOWN_TAG", severity="warning", message=f"Unknown tag found: {unk}"))
            
        # v tag
        if "v" not in tags:
            issues.append(AnalysisIssue(code="MISSING_VERSION", severity="error", message="Mandatory 'v' tag is missing."))
        elif tags.get("v") != "DMARC1":
            issues.append(AnalysisIssue(code="INVALID_VERSION", severity="error", message="DMARC version must be DMARC1."))
                
        # p tag
        policy = tags.get("p", "")
        if not policy:
            issues.append(AnalysisIssue(code="MISSING_POLICY", severity="error", message="Mandatory 'p' policy tag is missing."))
            return DmarcResult(
                exists=True, record=record, syntaxValid=syntax_valid, policy="", subdomainPolicy="", percentage=100,
                alignment=DmarcAlignment(dkim="", spf=""), reporting=DmarcReporting(rua=[], ruf=[]),
                issues=issues, warnings=warnings, tags=tags
            )
        elif policy not in ["none", "quarantine", "reject"]:
            issues.append(AnalysisIssue(code="INVALID_POLICY", severity="error", message=f"Invalid policy value: {policy}"))
            
        sub_policy = tags.get("sp", policy)
        if sub_policy not in ["none", "quarantine", "reject"] and sub_policy:
            issues.append(AnalysisIssue(code="INVALID_POLICY", severity="error", message=f"Invalid subdomain policy value: {sub_policy}"))
        
        pct_str = tags.get("pct", "100")
        try:
            pct = int(pct_str)
            if pct < 0 or pct > 100:
                raise ValueError()
        except ValueError:
            pct = 100
            issues.append(AnalysisIssue(code="INVALID_PERCENTAGE", severity="error", message=f"Invalid pct value: {pct_str}"))
            
        adkim = tags.get("adkim", "r")
        if adkim not in ["r", "s"]:
            issues.append(AnalysisIssue(code="INVALID_ALIGNMENT", severity="error", message=f"Invalid adkim value: {adkim}"))
            
        aspf = tags.get("aspf", "r")
        if aspf not in ["r", "s"]:
            issues.append(AnalysisIssue(code="INVALID_ALIGNMENT", severity="error", message=f"Invalid aspf value: {aspf}"))
            
        rua_raw = tags.get("rua", "")
        ruf_raw = tags.get("ruf", "")
        rua = [u.strip() for u in rua_raw.split(",") if u.strip()] if rua_raw else []
        ruf = [u.strip() for u in ruf_raw.split(",") if u.strip()] if ruf_raw else []
        
        return DmarcResult(
            exists=True,
            record=record,
            syntaxValid=syntax_valid,
            policy=policy,
            subdomainPolicy=sub_policy,
            percentage=pct,
            alignment=DmarcAlignment(dkim=adkim, spf=aspf),
            reporting=DmarcReporting(rua=rua, ruf=ruf),
            issues=issues,
            warnings=warnings,
            tags=tags
        )
        
    def _parse_record(self, record: str) -> Tuple[Dict[str, str], List[str], List[str], List[str]]:
        tags = {}
        duplicates = []
        syntax_errors = []
        unknown_tags = []
        known_tags = {"v", "p", "sp", "pct", "rua", "ruf", "adkim", "aspf", "fo", "ri"}
        
        parts = record.split(";")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if "=" not in part:
                 syntax_errors.append(f"Malformed tag (no '='): {part}")
                 continue
            key, val = part.split("=", 1)
            key = key.strip().lower()
            val = val.strip()
            
            if key in tags:
                duplicates.append(key)
            else:
                tags[key] = val
                if key not in known_tags:
                    unknown_tags.append(key)
                    
        return tags, duplicates, syntax_errors, unknown_tags
