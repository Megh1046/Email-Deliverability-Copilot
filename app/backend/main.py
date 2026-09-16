from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from domains.header_analysis.api import router as analysis_router

app = FastAPI(title="Email Deliverability Copilot API")

origins = [
    "http://localhost:3000",
]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api/v1")

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Email Deliverability Copilot backend is running"}
