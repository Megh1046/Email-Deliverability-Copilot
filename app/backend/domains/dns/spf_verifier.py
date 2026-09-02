import re
from typing import List, Set, Tuple
from .resolver import DNSResolver
from .schemas import SpfResult
from shared.models import AnalysisIssue
from domains.shared.constants import DNS_ERROR, INVALID_SYNTAX, LIMIT_EXCEEDED, MISSING_SPF, MULTIPLE_RECORDS

class SPFValidator:
    """Intelligent SPF record parser and validator."""

    def __init__(self, resolver: DNSResolver):
        self.resolver = resolver
        
    def analyze(self, domain: str) -> SpfResult:
        # Fetch TXT records from the same domain
        txt_records, err = self.resolver.lookup_record("TXT", domain)
        
        if err:
             return SpfResult(
                exists=False, record="", syntaxValid=False, lookupCount=0,
                issues=[AnalysisIssue(code=DNS_ERROR, severity="error", message=err)],
                warnings=[], mechanisms=[]
            )

        # Filter strictly for v=spf1 prefix
        spf_records = [
            r.replace('"', '').strip()
            for r in txt_records
            if r.replace('"', '').strip().lower().startswith("v=spf1")
       ]

        if not spf_records:
            return SpfResult(
                exists=False, record="", syntaxValid=False, lookupCount=0,
                issues=[AnalysisIssue(code=MISSING_SPF, severity="error", message="No SPF record found.")],
                warnings=[], mechanisms=[]
            )
            
        issues = []
        warnings = []
        if len(spf_records) > 1:
            issues.append(AnalysisIssue(code=MULTIPLE_RECORDS, severity="error", message="Multiple SPF records detected."))
            
        record = spf_records[0]
        mechanisms = self._parse_record(record)
        
        lookup_count, recursive_issues = self._evaluate_recursive(domain, set())
        issues.extend(recursive_issues)
        
        syntax_valid = True
        
        # Simple regex for valid mechanism prefixes
        mech_pattern = re.compile(r"^[+?~-]?(all|include:|a|mx|ptr|ip4:|ip6:|exists:|redirect=).*")
        
        for mech in mechanisms:
            mech_lower = mech.lower()
            if mech_lower != "v=spf1" and not mech_pattern.match(mech_lower):
                syntax_valid = False
                issues.append(AnalysisIssue(code=INVALID_SYNTAX, severity="error", message=f"Invalid mechanism syntax: {mech}"))
            
            clean = mech_lower.lstrip("+?~-")
            if clean == "ptr" or clean.startswith("ptr:"):
                warnings.append(AnalysisIssue(code="DEPRECATED_MECHANISM", severity="warning", message="PTR mechanism is deprecated."))

        if lookup_count > 10:
            issues.append(AnalysisIssue(code=LIMIT_EXCEEDED, severity="error", message=f"SPF record contains >10 DNS lookup mechanisms ({lookup_count})."))

        if not any(m.lower().endswith("all") for m in mechanisms):
            warnings.append(AnalysisIssue(code="MISSING_ALL", severity="warning", message="SPF record does not terminate with an 'all' mechanism."))

        return SpfResult(
            exists=True,
            record=record,
            syntaxValid=syntax_valid,
            lookupCount=lookup_count,
            issues=issues,
            warnings=warnings,
            mechanisms=mechanisms
        )
        
    def _parse_record(self, record: str) -> List[str]:
        return [m.strip() for m in record.split(" ") if m.strip()]

    def _evaluate_recursive(self, domain: str, visited: Set[str]) -> Tuple[int, List[AnalysisIssue]]:
        """Recursively evaluate SPF mechanisms to count DNS lookups.
        Follows RFC 7208 Section 4.6.4 logic for lookup limits."""
        if domain.lower() in visited:
            return 0, [AnalysisIssue(code=DNS_ERROR, severity="error", message=f"SPF recursion loop detected on domain: {domain}")]
        
        visited.add(domain.lower())
        
        txt_records, err = self.resolver.lookup_record("TXT", domain)
        if err:
            return 0, [AnalysisIssue(code=DNS_ERROR, severity="error", message=f"Failed to lookup SPF for include {domain}")]
            
        spf_records = [
            r.replace('"', '').strip()
            for r in txt_records
            if r.replace('"', '').strip().lower().startswith("v=spf1")
        ]
        
        if not spf_records:
            return 0, [AnalysisIssue(code=DNS_ERROR, severity="error", message=f"Included domain {domain} has no valid SPF record")]
            
        record = spf_records[0]
        mechanisms = self._parse_record(record)
        
        count = 0
        issues = []
        
        for mech in mechanisms:
            clean = mech.lower().lstrip("+?~-")
            
            # These mechanisms cost 1 lookup
            if clean.startswith(("include:", "a", "mx", "ptr", "exists:", "redirect=")):
                count += 1
                
                # Recursively evaluate includes and redirects
                if clean.startswith("include:"):
                    sub_domain = clean[8:]
                    sub_count, sub_issues = self._evaluate_recursive(sub_domain, visited)
                    count += sub_count
                    issues.extend(sub_issues)
                elif clean.startswith("redirect="):
                    sub_domain = clean[9:]
                    sub_count, sub_issues = self._evaluate_recursive(sub_domain, visited)
                    count += sub_count
                    issues.extend(sub_issues)
                    
        return count, issues
