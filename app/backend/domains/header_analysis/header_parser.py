"""
Backward-compatibility shim for the old HeaderParser.

WARNING: This module is deprecated. Please use the HeaderAnalysisPipeline
from .pipeline directly.
"""
import warnings

from .pipeline import HeaderAnalysisPipeline
from .schemas import HeaderAnalysisResponse

class HeaderParser:
    """
    Deprecated shim for HeaderParser.
    Delegates to the new HeaderAnalysisPipeline.
    """
    def __init__(self):
        warnings.warn(
            "HeaderParser is deprecated. Use HeaderAnalysisPipeline instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._pipeline = HeaderAnalysisPipeline()

    def parse(self, headers: str) -> HeaderAnalysisResponse:
        return self._pipeline.analyze(headers)
