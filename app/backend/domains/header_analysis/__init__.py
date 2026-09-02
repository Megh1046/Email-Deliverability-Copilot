"""
Email Authentication Troubleshooter pipeline.

Exposes the HeaderAnalysisPipeline as the primary entry point for analyzing
raw email headers and generating remediation steps.
"""
from .pipeline import HeaderAnalysisPipeline
from .schemas import HeaderAnalysisResponse

__all__ = ["HeaderAnalysisPipeline", "HeaderAnalysisResponse"]
