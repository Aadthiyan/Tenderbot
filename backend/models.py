"""
TenderBot Global — Pydantic Models
Request/Response schemas for FastAPI endpoints + MongoDB document shapes.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class TenderAction(str, Enum):
    apply_now = "apply_now"
    watch = "watch"
    skip = "skip"

class TenderStatus(str, Enum):
    active = "active"
    expired = "expired"
    applied = "applied"
    cancelled = "cancelled"
    unknown = "unknown"

class AlertType(str, Enum):
    new_match = "new_match"
    deadline_48h = "deadline_48h"
    amendment = "amendment"
    cancellation = "cancellation"
    sub_opportunity = "sub_opportunity"

class AlertChannel(str, Enum):
    slack = "slack"
    email = "email"
    voice = "voice"

class EligibilityStatus(str, Enum):
    pass_ = "pass"
    fail = "fail"
    unknown = "unknown"

class PortalKey(str, Enum):
    sam_gov = "sam_gov"
    ted_eu = "ted_eu"
    ungm = "ungm"
    find_a_tender = "find_a_tender"
    austender = "austender"
    canadabuys = "canadabuys"


# ── Company Profile ─────────────────────────────────────────────────────────────

class CompanyProfile(BaseModel):
    company_name: str
    website: Optional[str] = None
    headquarters_country: Optional[str] = None

    # Targeting
    sectors: List[str] = []               # e.g. ["Cloud", "AI", "Consulting"]
    keywords: List[str] = []              # e.g. ["cloud infrastructure", "SaaS"]
    target_countries: List[str] = []      # e.g. ["US", "EU", "UK"]
    min_value: Optional[float] = None     # USD
    max_value: Optional[float] = None     # USD
    agent_persona: Optional[str] = None   # Agent custom personality

    # Capability
    annual_turnover: Optional[float] = None
    headcount: Optional[int] = None
    years_in_business: Optional[int] = None
    certifications: List[str] = []        # e.g. ["ISO 9001", "SOC2"]
    past_contracts: List[str] = []        # brief descriptions

    # Portals & Notifications
    portals_enabled: List[PortalKey] = [
        PortalKey.sam_gov, PortalKey.ted_eu, PortalKey.ungm
    ]
    slack_webhook: Optional[str] = None
    alert_email: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Knowledge Base ─────────────────────────────────────────────────────────────

class KnowledgeBaseItem(BaseModel):
    id: Optional[str] = None              # hash(text)
    company_name: str
    text: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Eligibility ────────────────────────────────────────────────────────────────

class EligibilityCheckItem(BaseModel):
    requirement: str
    status: EligibilityStatus = EligibilityStatus.unknown
    gap: Optional[str] = None             # if status == fail


class EligibilityResult(BaseModel):
    eligibility_score: int = 0            # 0–100
    eligibility_checklist: List[EligibilityCheckItem] = []
    eligibility_action_plan: List[str] = []


# ── Amendment ─────────────────────────────────────────────────────────────────

class AmendmentEvent(BaseModel):
    at: datetime = Field(default_factory=datetime.utcnow)
    change_type: str                      # "deadline_extension" | "new_document" | "cancellation" | "scope_change"
    changes_summary: str
    new_deadline: Optional[datetime] = None
    is_cancelled: bool = False


# ── Tender ────────────────────────────────────────────────────────────────────

class Tender(BaseModel):
    tender_id: str                        # hash(title + agency + deadline)
    source_portal: PortalKey
    title: str
    agency: Optional[str] = None
    country: Optional[str] = None
    deadline: Optional[datetime] = None
    days_until_deadline: Optional[int] = None
    estimated_value: Optional[float] = None
    description: Optional[str] = None
    category_code: Optional[str] = None  # NAICS / CPV
    raw_url: str
    status: TenderStatus = TenderStatus.active

    # Scoring (populated after Fireworks.ai call)
    relevance_score: Optional[int] = None
    match_reasons: List[str] = []
    disqualifiers: List[str] = []
    action: Optional[TenderAction] = None

    # Deep enrichment (populated after TinyFish deep scrape)
    enriched: bool = False
    eligibility_requirements: List[str] = []
    submission_format: Optional[str] = None
    contact_email: Optional[str] = None
    evaluation_criteria: Optional[str] = None

    # Eligibility analysis (populated after Fireworks.ai eligibility call)
    eligibility_score: Optional[int] = None
    eligibility_checklist: List[EligibilityCheckItem] = []
    eligibility_action_plan: List[str] = []

    # Competitor intel (P2 feature — populated later)
    top_competitors: List[str] = []
    our_win_probability: Optional[float] = None
    winning_strategy: Optional[str] = None

    # Amendments
    amendment_history: List[AmendmentEvent] = []

    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    page_snapshot: Optional[str] = None  # for amendment diff


# ── Portal Log ────────────────────────────────────────────────────────────────

class PortalLog(BaseModel):
    portal: PortalKey
    run_at: datetime = Field(default_factory=datetime.utcnow)
    status: str                           # "success" | "failed" | "timeout" | "partial"
    tenders_found: int = 0
    duration_ms: Optional[int] = None
    error: Optional[str] = None


# ── Alert ─────────────────────────────────────────────────────────────────────

class Alert(BaseModel):
    tender_id: str
    user_id: str
    alert_type: AlertType
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    channel: AlertChannel
    delivered: bool = True
    message_preview: Optional[str] = None


# ── API Request / Response Bodies ─────────────────────────────────────────────

class ProfileRequest(BaseModel):
    profile: CompanyProfile

class ScrapeRequest(BaseModel):
    user_id: str
    portals: Optional[List[PortalKey]] = None   # None = all enabled portals

class AlertConfigRequest(BaseModel):
    user_id: str
    slack_webhook: Optional[str] = None
    alert_email: Optional[str] = None

class TenderListResponse(BaseModel):
    total: int
    tenders: List[Dict[str, Any]]

class ScrapeStatusResponse(BaseModel):
    status: str
    message: str
    portals_triggered: List[str]

class HealthPortalStatus(BaseModel):
    portal: str
    status: str                           # "healthy" | "degraded" | "down" | "unknown"
    success_rate_pct: Optional[float] = None
    last_run: Optional[datetime] = None
    last_error: Optional[str] = None

class HealthResponse(BaseModel):
    overall: str
    portals: List[HealthPortalStatus]
    scheduler_running: bool
    api_keys: Dict[str, bool]
    checked_at: datetime = Field(default_factory=datetime.utcnow)

class AutoFillRequest(BaseModel):
    tender_id: str
    user_id: str

class AutoFillResponse(BaseModel):
    fields_filled: List[str]
    fields_remaining: List[str]
    completion_pct: float
