"""
TenderBot Global — Dependencies
Reusable FastAPI dependencies (like tenant isolation auth).
"""
from fastapi import Header, HTTPException
import logging

logger = logging.getLogger(__name__)

def verify_tenant_header(x_company_name: str = Header(None)) -> str:
    """Verifies that the request includes the X-Company-Name header."""
    if not x_company_name:
        logger.warning("Blocked request: Missing X-Company-Name header.")
        raise HTTPException(
            status_code=401, 
            detail="Tenant isolation requires X-Company-Name header."
        )
    return x_company_name
