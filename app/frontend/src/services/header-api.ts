import { HeaderAnalysisRequest, HeaderAnalysisResponse } from '../types/header-analysis';

export async function analyzeHeaders(
  rawHeaders: string,
  providerHint?: string,
  spfMode?: 'relaxed' | 'strict',
  dkimMode?: 'relaxed' | 'strict'
): Promise<HeaderAnalysisResponse> {
  try {
    const payload: HeaderAnalysisRequest = {
      headers: rawHeaders,
      ...(providerHint && { provider_hint: providerHint }),
      ...(spfMode && { spf_alignment_mode: spfMode }),
      ...(dkimMode && { dkim_alignment_mode: dkimMode }),
    };

    const response = await fetch('/api/v1/analysis/headers', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let errorMessage = 'An unexpected error occurred.';
      try {
        const errorData = await response.json();
        // The backend returns a detail array for validation errors (e.g. 422)
        if (errorData?.detail && Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((e: any) => e.msg).join(', ');
        } else if (errorData?.detail) {
            errorMessage = errorData.detail;
        } else {
            errorMessage = `Server error: ${response.status}`;
        }
      } catch (e) {
        errorMessage = `Server error: ${response.status}`;
      }
      throw new Error(errorMessage);
    }

    const data: HeaderAnalysisResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Error analyzing headers:', error);
    throw error;
  }
}
