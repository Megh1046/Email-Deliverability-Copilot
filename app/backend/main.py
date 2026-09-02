from fastapi import FastAPI
from domains.header_analysis.api import router as analysis_router

app = FastAPI(title="Email Deliverability Copilot API")

app.include_router(analysis_router, prefix="/api/v1")

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Email Deliverability Copilot backend is running"}
