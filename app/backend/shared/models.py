from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

class BaseApiResponse(BaseModel):
    version: str = Field(default="1.0")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requestId: str = Field(default_factory=lambda: str(uuid.uuid4()))

class FullAnalysisRequest(BaseModel):
    domain: str = Field(..., description="The domain for analysis")
    selector: str | None = Field(None, description="The DKIM selector to query")
class AnalysisIssue(BaseModel):
    code: str
    severity: str
    message: str


class DomainRequest(BaseModel):
    domain: str
    selector: str | None = None