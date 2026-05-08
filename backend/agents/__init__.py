"""TenderBot Global — Agents Package

Procurement Discovery Agents:
  Government Portals (6):
    - SAM.gov (US government contracts)
    - TED EU (European tenders)
    - UNGM (UN global procurement)
    - Find a Tender (UK government)
    - AusTender (Australian procurement)
    - CanadaBuys (Canadian government)
  
  US Regional & Local (3):
    - SBA (Small Business Administration set-asides)
    - California (California state procurement)
    - Local Government (City/county contracts from major metros)
  
  Internet-Wide (2):
    - Web Search (Google/Bing search for opportunities)
    - Alternative Sources (LinkedIn, private bidding platforms, marketplaces)
"""

from backend.agents.sam_gov import run_sam_gov_agent
from backend.agents.ted_eu import run_ted_eu_agent
from backend.agents.ungm import run_ungm_agent
from backend.agents.find_a_tender import run_find_a_tender_agent
from backend.agents.austender import run_austender_agent
from backend.agents.canadabuys import run_canadabuys_agent
from backend.agents.web_search import run_web_search_agent
from backend.agents.alternative_sources import run_alternative_sources_agent
from backend.agents.sba import run_sba_agent
from backend.agents.california import run_california_agent
from backend.agents.local_government import run_local_government_agent

__all__ = [
    "run_sam_gov_agent",
    "run_ted_eu_agent",
    "run_ungm_agent",
    "run_find_a_tender_agent",
    "run_austender_agent",
    "run_canadabuys_agent",
    "run_web_search_agent",
    "run_alternative_sources_agent",
    "run_sba_agent",
    "run_california_agent",
    "run_local_government_agent",
]


