"""
TenderBot Global — Portal Configurations
Natural-language TinyFish goals for each of the 6 government portals.
"""

PORTAL_CONFIGS: dict[str, dict] = {

    "sam_gov": {
        "url": "https://sam.gov/search/?index=opp&q={kw}&dateRange=custom&startDate={30d_ago}&endDate={today}&status=active",
        "goal": """
            You are searching SAM.gov for active US government procurement opportunities.
            Search keyword: '{kw}'.
            
            Steps:
            1. If a cookie consent or popup appears, dismiss it.
            2. Wait for search results to load.
            3. Apply filter: Status = Active / Open.
            4. For each result on the first {max_pages} pages, extract:
               - title: the opportunity title
               - agency: the issuing agency name
               - naics_code: NAICS code if visible
               - deadline: response/close date
               - award_value: estimated contract value if shown
               - place_of_performance: primary location (use "US" if not shown)
               - solicitation_number: the solicitation/notice ID
               - description: brief description or synopsis (first 300 chars)
               - url: the direct link to this opportunity
            5. Navigate to next page and repeat until {max_pages} pages done.
            6. Return as a JSON array. Each element must have all keys above.
               Use null for any missing values.
            7. Do not open individual tender pages — only extract from the listing.
        """,
        "auth_required": False,
        "handles": ["cookie_popups", "pagination", "dynamic_filters"],
        "country": "US",
    },

    "ted_eu": {
        "url": "https://ted.europa.eu/en/search?q={kw}&scope=ALL&sortColumn=ND_OJ&sortOrder=desc",
        "goal": """
            You are searching TED (Tenders Electronic Daily) for EU procurement notices.
            Search keyword: '{kw}'.
            
            Steps:
            1. Accept/close the cookie consent banner if it appears.
            2. Wait for search results to load.
            3. For each result on the first {max_pages} pages, extract:
               - title: tender title (prefer English if shown)
               - contracting_authority: the buyer/authority name
               - country: the country of the contracting authority
               - cpv_code: CPV code if available
               - deadline: the submission/closing date
               - estimated_value: contract value (pick EUR amount)
               - procedure_type: open, restricted, negotiated etc.
               - language: primary language of the notice
               - url: link to the full notice
            4. Navigate to the next page if needed.
            5. Return as a JSON array with all keys. Use null for missing values.
            6. Do not enter individual tender pages.
        """,
        "auth_required": False,
        "handles": ["cookie_modal", "multilingual", "pagination"],
        "country": "EU",
    },

    "ungm": {
        "url": "https://www.ungm.org/Public/Notice",
        "goal": """
            You are browsing the UNGM (United Nations Global Marketplace) notice board.
            Search keyword: '{kw}'.
            
            Steps:
            1. Look for a search or filter field and enter '{kw}'.
            2. Apply filter to show only Open notices.
            3. For each of the first 10 notices, extract:
               - reference_number: the unique notice reference
               - title: full notice title
               - organization: UN agency or body issuing the notice
               - deadline: the closing/submission deadline date
               - category: procurement category or type
               - description: brief description (first 300 chars)
               - url: link to the notice detail page
            4. Return as a JSON array. Use null for missing fields.
        """,
        "auth_required": False,
        "handles": ["dynamic_filters", "session_state"],
        "country": "UN",
    },

    "find_a_tender": {
        "url": "https://www.find-a-tender.service.gov.uk/Search?keywords={kw}&status=live",
        "goal": """
            You are searching Find a Tender (UK government) for live procurement opportunities.
            Search keyword: '{kw}'.
            
            Steps:
            1. Wait for results to load.
            2. For each result on the first {max_pages} pages, extract:
               - title: opportunity title
               - buyer_name: the buying organisation
               - published_date: when it was published
               - closing_date: submission deadline
               - contract_value: estimated or maximum value
               - cpv_codes: CPV classification codes
               - procedure: procurement procedure type
               - url: direct link to this notice
            3. Navigate to next page as needed.
            4. Return as JSON array. All keys required; use null if absent.
        """,
        "auth_required": False,
        "handles": ["pagination", "dynamic_UI"],
        "country": "UK",
    },

    "austender": {
        "url": "https://www.tenders.gov.au/?event=public.atm.list",
        "goal": """
            You are searching AusTender for Australian government tender opportunities.
            Search keyword: '{kw}'.
            
            Steps:
            1. Find the search / filter form and enter keyword '{kw}'.
            2. Filter for Open ATMs (Approach to Market).
            3. For each of the first 10 results, extract:
               - atm_id: the ATM ID / reference
               - title: tender title
               - agency: issuing Australian government agency
               - close_date: closing date for submissions
               - value: estimated contract value if visible
               - category: procurement category
               - state: Australian state/territory
               - url: link to the ATM listing
            4. Return as JSON array with all keys. Use null for missing values.
        """,
        "auth_required": False,
        "handles": ["form_fills", "session_management"],
        "country": "AU",
    },

    "canadabuys": {
        "url": "https://canadabuys.canada.ca/en/tender-opportunities?q={kw}&status=1",
        "goal": """
            You are searching CanadaBuys for open Canadian government tender opportunities.
            Search keyword: '{kw}'.
            
            Steps:
            1. Wait for results to load. Dismiss any cookie/consent banners.
            2. Filter to show only Open opportunities.
            3. For each result on the first {max_pages} pages, extract:
               - solicitation_number: the solicitation identifier
               - title: tender title
               - department: issuing government department
               - closing_date: submission deadline
               - procurement_category: category of procurement
               - region: Canadian province or national
               - url: direct link to the tender
            4. Navigate next pages as needed.
            5. Return as JSON array. Use null for missing values.
        """,
        "auth_required": False,
        "handles": ["pagination", "bilingual_UI"],
        "country": "CA",
    },
}

# Deep RFP scraper goal template
DEEP_SCRAPE_GOAL = """
    You are reading the full details of a government tender/RFP page.
    URL: {url}
    
    Steps:
    1. Navigate to the URL.
    2. Dismiss any cookie banners or login prompts (do not log in).
    3. If there is a "View Details", "Full Notice", or "Documents" button, click it.
    4. If there is a "Download Documents" section visible, list the document names and sizes
       but do NOT download them.
    5. Extract the following in full detail:
       - eligibility_requirements: list every explicit eligibility criterion (registration,
         turnover, certifications, years in business, geographic restrictions)
       - required_certifications: any specific standards or accreditations required
       - evaluation_criteria: scoring methodology (e.g. 70% technical, 30% price)
       - submission_format: what must be submitted, how, and where
       - contact_email: procurement officer email if visible
       - contact_name: procurement officer name if visible
       - pre_bid_meeting: date/details of any pre-bid briefing
       - amendment_notes: any visible amendment or addendum notices
       - pdf_attachments: list of absolute URLs for any .pdf links found on the page
       - page_snapshot: a plain-text summary of the full page content (max 2000 chars)
    6. Return as a single JSON object with all the above keys. Use null for missing fields.
    7. Do NOT click to download files — just extract the direct URLs.
"""

# Amendment tracker goal template
AMENDMENT_GOAL = """
    You are re-visiting a government tender page to check for updates.
    URL: {url}
    
    Compare the current page to this previous snapshot:
    ---SNAPSHOT---
    {snapshot}
    ---END SNAPSHOT---
    
    Detect meaningful changes:
    - Has the deadline/closing date changed?
    - Are there new documents or attachments?
    - Have the requirements or scope changed?
    - Has the tender been cancelled or suspended?
    - Are there any new clarification/amendment notices?
    
    Return a JSON object:
    {{
      "has_changes": true/false,
      "change_type": "deadline_extension|new_document|scope_change|cancellation|clarification|none",
      "changes_summary": "one-sentence description of what changed",
      "new_deadline": "ISO date string or null",
      "is_cancelled": true/false,
      "page_snapshot": "updated plain-text summary of page (max 2000 chars)"
    }}
"""

# Form-fill goal template
FORM_FILL_GOAL = """
    You are assisting a company to pre-fill a government tender application form.
    Application page URL: {url}
    
    Company profile data:
    {profile_json}
    
    Steps:
    1. Navigate to the application page.
    2. Identify all input fields in the form.
    3. For each field, check if the company profile contains a semantically matching value:
       - Company name → company_name
       - Registration number → any registration_id field in profile
       - Address → any address field in profile
       - Contact email → alert_email
       - Annual turnover → annual_turnover
       - Headcount → headcount
       - Years in business → years_in_business
       - Certifications → certifications list
    4. Fill ONLY fields you have clear data for. Do NOT guess or fabricate values.
    5. Do NOT click any submit, send, or confirm button.
    6. Report your work as JSON:
    {{
      "fields_filled": ["field_label_1", "field_label_2", ...],
      "fields_remaining": ["field_label_3", ...],
      "completion_pct": 0.0-100.0
    }}
"""

# Competitor intel goal template
COMPETITOR_INTEL_GOAL = """
    You are researching past government contract awards.
    Search query/URL: {url}
    
    Steps:
    1. Look for recently awarded contracts similar to the search query '{kw}'.
    2. Extract information about the awarded vendors.
    3. Return a JSON object with a list of past winners:
    {{
       "past_awards": [
         {{
           "winner_name": "Name of winning company",
           "award_value": 1500000,
           "award_date": "YYYY-MM-DD"
         }}
       ]
    }}
    If no past awards are visible, return an empty array for past_awards.
"""

# Subcontractor Radar goal template
SUBCONTRACTOR_RADAR_GOAL = """
    You are searching for subcontractor or partnering opportunities on a primary contractor hub.
    Search query/URL: {url}
    
    Steps:
    1. Search the page for "Subcontractor", "Teaming", "Partner", or "Opportunities".
    2. Look for open requests where a Prime Vendor is looking for Small Business or technical partners for a larger contract.
    3. Extract any relevant sub-bidding opportunities matching '{kw}'.
    4. Return a JSON object with a list of opportunities:
    {{
       "sub_opportunities": [
         {{
           "prime_contractor": "Name of the Prime (e.g. Lockheed, Boeing, etc)",
           "project_title": "Name of the major project",
           "sub_role_needed": "The specific task/role they are subcontracting (e.g. Cyber Assessment)",
           "contact_info": "Email or URL to apply for teaming",
           "deadline": "YYYY-MM-DD"
         }}
       ]
    }}
    Use null for missing fields. Return empty array if none found.
"""
