import base64
from typing import Dict, Tuple, List
from .resolver import DNSResolver
from .schemas import DkimResult
from shared.models import AnalysisIssue
from domains.shared.constants import DNS_ERROR, INVALID_DKIM_RECORD, INVALID_SYNTAX, MISSING_DKIM, MULTIPLE_RECORDS

class DKIMValidator:
    """Intelligent DKIM record parser and validator."""

    def __init__(self, resolver: DNSResolver):
        self.resolver = resolver
        
    def analyze(self, domain: str, selector: str) -> DkimResult:
        dkim_domain = f"{selector}._domainkey.{domain}"
        txt_records, err = self.resolver.lookup_record("TXT", dkim_domain)
        
        if err:
             return DkimResult(
                exists=False, selector=selector, record="", syntaxValid=False, keyType="",
                status="ERROR",
                issues=[AnalysisIssue(code=DNS_ERROR, severity="error", message=err)],
                warnings=[], tags={}
            )

        # A selector can contain unrelated TXT data.  A key record must declare
        # DKIM1 or expose p=; SPF and arbitrary TXT records are never DKIM keys.
        dkim_records = []
        for raw_record in txt_records:
            normalized = raw_record.replace('"', '').strip()
            lower = normalized.lower().replace(" ", "")
            if lower.startswith("v=spf1"):
                continue
            tags, _, _, _ = self._parse_record(normalized)
            if tags.get("v", "").upper() == "DKIM1" or "p" in tags:
                dkim_records.append(normalized)
        
        if not dkim_records:
            issue = (
                AnalysisIssue(code=INVALID_DKIM_RECORD, severity="error", message="TXT records exist for this selector but none is a DKIM key.")
                if txt_records else
                AnalysisIssue(code=MISSING_DKIM, severity="error", message="No DKIM record found for this selector.")
            )
            return DkimResult(
                exists=False, selector=selector, record="", syntaxValid=False, keyType="",
                status="INVALID" if txt_records else "MISSING",
                issues=[issue],
                warnings=[], tags={}
            )
            
        issues = []
        warnings = []
        if len(dkim_records) > 1:
            issues.append(AnalysisIssue(code=MULTIPLE_RECORDS, severity="error", message="Multiple DKIM records detected."))
            
        record = dkim_records[0]
        tags, duplicate_tags, syntax_errors, unknown_tags = self._parse_record(record)
        
        syntax_valid = len(syntax_errors) == 0 and len(duplicate_tags) == 0

        for dup in duplicate_tags:
            issues.append(AnalysisIssue(code="DUPLICATE_TAG", severity="error", message=f"Duplicate tag found: {dup}"))
        for stx in syntax_errors:
            issues.append(AnalysisIssue(code=INVALID_SYNTAX, severity="error", message=stx))
        for unk in unknown_tags:
            warnings.append(AnalysisIssue(code="UNKNOWN_TAG", severity="warning", message=f"Unknown tag found: {unk}"))
            
        key_type = tags.get("k", "rsa").lower()
        if key_type not in ["rsa", "ed25519"]:
            issues.append(AnalysisIssue(code="UNSUPPORTED_KEY", severity="error", message=f"Unsupported key type: {key_type}"))

        public_key = tags.get("p", "")
        key_length = None
        if not public_key:
            issues.append(AnalysisIssue(code="MISSING_KEY", severity="error", message="Required public key (p=) is missing or empty."))
        else:
            try:
                decoded = base64.b64decode(public_key)
                if key_type == "rsa":
                    # RSA key in DNS is ASN.1 DER encoded SubjectPublicKeyInfo.
                    # It has ~38 bytes of overhead (sequence headers, OID).
                    # A 2048-bit (256-byte) key will be ~294 bytes DER encoded.
                    estimated_bits = (len(decoded) - 38) * 8
                    # Snap to standard key sizes due to minor ASN.1 length variations
                    if 1000 <= estimated_bits <= 1050: key_length = 1024
                    elif 2000 <= estimated_bits <= 2100: key_length = 2048
                    elif 4000 <= estimated_bits <= 4150: key_length = 4096
                    else: key_length = estimated_bits
                elif key_type == "ed25519":
                    key_length = 256
            except Exception:
                issues.append(AnalysisIssue(code="INVALID_KEY", severity="error", message="Public key is not valid base64."))

        if tags.get("v") != "DKIM1":
            issues.append(AnalysisIssue(code="INVALID_VERSION", severity="error", message="DKIM version must be DKIM1."))

        return DkimResult(
            exists=True,
            selector=selector,
            record=record,
            syntaxValid=syntax_valid,
            keyType=key_type,
            keyLength=key_length,
            status="VERIFIED",
            issues=issues,
            warnings=warnings,
            tags=tags
        )
        
    def _parse_record(self, record: str) -> Tuple[Dict[str, str], List[str], List[str], List[str]]:
        tags = {}
        duplicates = []
        syntax_errors = []
        unknown_tags = []
        known_tags = {"v", "k", "p", "t", "n", "h", "s", "g", "a", "x"}
        
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
