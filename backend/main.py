"""
TenderBot Global — FastAPI Application Entry Point
All routers, CORS, lifespan (DB connect + scheduler).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import agentops
import logging
import os

from backend.config import get_settings
from backend.services.db import connect_db, close_db
from backend.scheduler import start_scheduler, get_scheduler
from backend.routers import health, profile, scrape, tenders, alerts, briefing, agents, ws_route
from backend.services.ws import manager

# ── Windows UTF-8 fix (emoji in 3rd-party logs like AgentOps) ────────────────
import sys, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("🚀 TenderBot Global starting up...")

    # 1. Connect to MongoDB (non-fatal)
    try:
        await connect_db()
    except Exception as db_err:
        logger.error(f"❌ DB startup error (continuing anyway): {db_err}")

    # 2. Initialise AgentOps monitoring
    if settings.agentops_api_key:
        agentops.init(api_key=settings.agentops_api_key, auto_start_session=False)
        logger.info("✅ AgentOps initialised.")

    # 3. Start APScheduler background jobs
    start_scheduler()

    # 4. Ensure audio directory exists (for ElevenLabs briefings)
    os.makedirs(os.path.join(os.path.dirname(__file__), "audio"), exist_ok=True)

    # 5. Start WebSocket Redis Pub/Sub listener
    if hasattr(settings, "celery_broker_url"):
        await manager.start_redis_listener(settings.celery_broker_url)

    logger.info("✅ TenderBot Global ready.")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("🛑 TenderBot Global shutting down...")
    sched = get_scheduler()
    if sched.running:
        sched.shutdown(wait=False)
    await manager.close()
    await close_db()


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="TenderBot Global API",
    description=(
        "Autonomous multi-portal government tender discovery. "
        "Powered by TinyFish web agents, Fireworks.ai LLM, and MongoDB Atlas."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(profile.router)
app.include_router(scrape.router)
app.include_router(tenders.router)
app.include_router(alerts.router)
app.include_router(briefing.router)
app.include_router(agents.router)
app.include_router(ws_route.router)

# ── Static Files ──────────────────────────────────────────────────────────────
static_path = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")


# ── Root Ping ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "TenderBot Global API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }
