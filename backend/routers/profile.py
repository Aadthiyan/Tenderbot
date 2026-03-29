"""
TenderBot Global — /profile Router
Save and retrieve company profiles.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from datetime import datetime
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.db import users_col, knowledge_base_col
from backend.models import ProfileRequest, CompanyProfile
from backend.services.knowledge_base import add_to_knowledge_base
from backend.dependencies import verify_tenant_header
import logging

router = APIRouter(prefix="/profile", tags=["Profile"])
logger = logging.getLogger(__name__)


@router.post("", status_code=201)
async def save_profile(req: ProfileRequest):
    """
    Save or update a company profile.
    For v1 hackathon: single-user, identified by company_name.
    Returns the stored profile with its MongoDB _id.
    """
    profile_dict = req.profile.model_dump()
    profile_dict["updated_at"] = datetime.utcnow()

    result = await users_col().update_one(
        {"company_name": req.profile.company_name},
        {"$set": profile_dict, "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True,
    )

    # Fetch and return the stored document
    stored = await users_col().find_one(
        {"company_name": req.profile.company_name},
        {"_id": 0}
    )
    return {"status": "ok", "profile": stored}


@router.get("/{company_name}")
async def get_profile(company_name: str):
    """Retrieve a company profile by name."""
    profile = await users_col().find_one(
        {"company_name": company_name},
        {"_id": 0}
    )
    if not profile:
        profile = {"company_name": company_name, "agent_persona": ""}
        await users_col().insert_one(profile.copy())
        if "_id" in profile:
            del profile["_id"]
    return profile


@router.post("/knowledge", status_code=201)
async def ingest_knowledge(company_name: str, text: str, tenant: str = Depends(verify_tenant_header)):
    """
    Ingest a piece of internal company knowledge (text).
    The service will handle embedding and storing in the Vector DB.
    """
    if company_name != tenant:
        raise HTTPException(status_code=403, detail="Tenant isolation violation.")

    try:
        result = await add_to_knowledge_base(company_name, text)
        if result["inserted"]:
            return {"status": "ok", "message": f"Added {result['chunks']} chunks for '{company_name}'"}
        else:
            return {"status": "duplicate", "message": "This content is already in your knowledge base."}
    except Exception as e:
        logger.error(f"Failed to ingest knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/file", status_code=201)
async def upload_knowledge_file(company_name: str, file: UploadFile = File(...), tenant: str = Depends(verify_tenant_header)):
    """
    Upload a PDF file to ingest in the company knowledge base.
    """
    if company_name != tenant:
        raise HTTPException(status_code=403, detail="Tenant isolation violation.")
        
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        content = await file.read()
        text = extract_text_from_pdf(content)

        if not text:
            raise HTTPException(status_code=422, detail="Failed to extract text from PDF.")

        result = await add_to_knowledge_base(company_name, text, metadata={"filename": file.filename})
        if result["inserted"]:
            return {"status": "ok", "message": f"File '{file.filename}' ingested ({result['chunks']} chunks)"}
        else:
            return {"status": "duplicate", "message": f"'{file.filename}' is already in your knowledge base."}
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/{company_name}")
async def get_company_knowledge(company_name: str, tenant: str = Depends(verify_tenant_header)):
    """
    List all knowledge items for a company.
    """
    if company_name != tenant:
        raise HTTPException(status_code=403, detail="Tenant isolation violation.")
        
    cursor = knowledge_base_col().find({"company_name": company_name}, {"embedding": 0})
    items = await cursor.to_list(length=100)
    for item in items:
        item["_id"] = str(item["_id"])
    return items

@router.get("/audit-logs/{company_name}")
async def get_audit_logs(company_name: str, tenant: str = Depends(verify_tenant_header)):
    """Fetch audit logs of when private data was accessed."""
    if company_name != tenant:
        raise HTTPException(status_code=403, detail="Tenant isolation violation.")
    
    from backend.services.db import audit_logs_col
    cursor = audit_logs_col().find({"company_name": company_name}).sort("accessed_at", -1).limit(50)
    items = await cursor.to_list(length=50)
    for item in items:
        item["_id"] = str(item["_id"])
    return items
