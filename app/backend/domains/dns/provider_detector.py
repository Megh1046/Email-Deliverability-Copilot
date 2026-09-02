from typing import List, Dict, Tuple, Optional
from .schemas import SpfResult

# Provider Fingerprint Catalog
PROVIDER_CATALOG = {
    "Google Workspace": {
        "mx": ["aspmx.l.google.com"],
        "spf": ["_spf.google.com"],
        "selectors": ["google"]
    },
    "Microsoft 365": {
        "mx": ["mail.protection.outlook.com"],
        "spf": ["spf.protection.outlook.com"],
        "selectors": ["selector1", "selector2"]
    },
    "SendGrid": {
        "mx": ["mx.sendgrid.net"],
        "spf": ["sendgrid.net"],
        "selectors": ["s1", "s2"]
    },
    "Mailchimp": {
        "mx": [],
        "spf": ["servers.mcsv.net", "spf.mandrillapp.com"],
        "selectors": ["k1", "k2", "k3"]
    },
    "Mailgun": {
        "mx": ["mxa.mailgun.org"],
        "spf": ["mailgun.org"],
        "selectors": ["pic", "krs", "mg", "mailo"]
    },
    "Zendesk": {
        "mx": [],
        "spf": ["mail.zendesk.com"],
        "selectors": ["zendesk1", "zendesk2"]
    },
    "Amazon SES": {
        "mx": ["smtp.receptor.amazon.com", "inbound-smtp.amazonaws.com"],
        "spf": ["amazonses.com"],
        "selectors": []  # SES uses custom 32-char selectors; dictionary fallback applies
    }
}

DICTIONARY_CATALOG = [
    "default", "mail", "api", "smtp", "s1", "k1", "m1", "dkim"
]

class DKIMDiscoveryService:
    """Service to discover candidate DKIM selectors based on DNS and SPF context."""

    def discover_selectors(self, domain: str, dns_records: Dict[str, List[str]], spf_result: SpfResult, provided_selector: Optional[str] = None) -> Tuple[List[str], Optional[str]]:
        """
        Returns a prioritized list of selectors to try, and the name of the identified provider (if any).
        Selector discovery is intentionally conservative.  DKIM selectors are
        not enumerable in DNS, so guesses are hints, not proof.
        """
        selectors = []
        identified_provider = None
        
        # 1. Provided selector has highest priority
        if provided_selector:
            selectors.append(provided_selector)
            
        # `lookup_all` returns {"records": {"mx": [...]}}. Accept the inner
        # records map too so this service remains reusable and testable.
        records = dns_records.get("records", dns_records)
        mx_records = records.get("mx", records.get("MX", []))
        
        for provider, footprint in PROVIDER_CATALOG.items():
            matched = False
            
            # Check MX footprint
            for mx_footprint in footprint["mx"]:
                for record in mx_records:
                    if mx_footprint.lower() in record.lower():
                        matched = True
                        break
                if matched:
                    break
            
            # Check SPF footprint
            if not matched:
                for spf_footprint in footprint["spf"]:
                    for mech in spf_result.mechanisms:
                        if spf_footprint.lower() in mech.lower():
                            matched = True
                            break
                    if matched:
                        break
                    
            if matched:
                identified_provider = provider
                break # Only map to the first matched primary provider

        # Do not probe common selector dictionaries. A failed guess means only
        # that the guess was wrong and previously produced false negatives.
        return selectors[:1], identified_provider
