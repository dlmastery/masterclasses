"""Acme claims-status REST API (FastAPI). It serves /openapi.json.

Run: CLAIMS_API_KEY=demo-key-123 uvicorn claims_api:app --port 8081
"""
import os

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

app = FastAPI(title="Claims Status API",
              servers=[{"url": "http://127.0.0.1:8081"}])
api_key = APIKeyHeader(name="X-API-Key")
STATUS = {"CLM-1001": {"stage": "in_review", "adjuster": "R. Patel",
                       "next_step": "2026-10-26"}}


def check_key(key: str = Security(api_key)) -> None:
    if key != os.environ.get("CLAIMS_API_KEY", "demo-key-123"):
        raise HTTPException(status_code=401, detail="bad api key")


@app.get("/claims/{claim_id}", operation_id="getClaimStatus",
         dependencies=[Depends(check_key)])
def get_claim_status(claim_id: str) -> dict:
    """Get the review stage, adjuster and next step for a claim."""
    if claim_id not in STATUS:
        raise HTTPException(status_code=404, detail="unknown claim")
    return STATUS[claim_id]
