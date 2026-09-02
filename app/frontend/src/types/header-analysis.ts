export interface AuthEvidence {
  authserv_id: string | null;
  spf_result: string | null;
  spf_domain: string | null;
  dkim_result: string | null;
  dkim_domain: string | null;
  dkim_selector: string | null;
  dmarc_result: string | null;
  raw: string;
}

export interface AuthenticationResult {
  result: 'PASS' | 'FAIL' | 'UNKNOWN';
  raw_result: string | null;
  domain: string | null;
  selector: string | null;
}

export interface AlignmentResult {
  spf: boolean | null;
  dkim: boolean | null;
  overall: boolean | null;
  spf_mode: 'relaxed' | 'strict';
  dkim_mode: 'relaxed' | 'strict';
}

export interface RootCause {
  code: string;
  title: string;
  description: string;
  protocol: 'SPF' | 'DKIM' | 'DMARC' | 'NONE';
}

export interface RemediationStep {
  step: number;
  action: string;
  detail: string | null;
  sample_record: string | null;
  validation_cmd: string | null;
}

export interface ProviderInfo {
  name: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface HeaderAnalysisResponse {
  spf: AuthenticationResult;
  dkim: AuthenticationResult;
  dmarc: AuthenticationResult;
  alignment: AlignmentResult;
  from_domain: string | null;
  return_path_domain: string | null;
  dkim_signing_domain: string | null;
  authentication_results: string[];
  evidence: AuthEvidence[];
  root_cause: RootCause | null;
  remediation: RemediationStep[];
  provider: ProviderInfo | null;
  passed: boolean;
  failure_summary: string | null;
}

export interface HeaderAnalysisRequest {
  headers: string;
  provider_hint?: string;
  spf_alignment_mode?: 'relaxed' | 'strict';
  dkim_alignment_mode?: 'relaxed' | 'strict';
}
