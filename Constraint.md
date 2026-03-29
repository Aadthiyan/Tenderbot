"TenderBot monitors government procurement portals across 50+ countries — UN, World Bank, EU, US SAM.gov, India GeM, UK Find-a-Tender — matches tenders to your business profile, pre-fills applications, and alerts you before deadlines. The world's $13T government contract market, automated."

International Portals TinyFish Navigates
Region	Portal	Complexity
🌐 Global	UNGM (ungm.org) — UN procurement	Login wall, pagination, filters
🌐 Global	World Bank STEP (worldbank.org/procurement)	Dynamic search, document downloads
🇺🇸 USA	SAM.gov — Federal contracts	Multi-step filters, pop-ups, auth
🇪🇺 EU	TED (ted.europa.eu) — EU tenders	Pagination, multilingual, dynamic UI
🇬🇧 UK	Find a Tender (find-a-tender.service.gov.uk)	Session management, form fills
🇦🇺 AU	AusTender (tenders.gov.au)	Category filters, document portals
🇨🇦 CA	CanadaBuys (canadabuys.canada.ca)	Multi-step, form-heavy
🇮🇳 IN	GeM + eProcure	CAPTCHA, login, pagination
🌍 Africa	African Development Bank procurement portal	Dynamic UI, document downloads
Every single one of these has zero public API — pure browser-only access, maximizing your TinyFish tech score. [query]
​

Why International = Stronger on All 3 Criteria
Tech (50%): 8+ portals across languages, auth systems, UI frameworks, pagination styles — judges see genuine complexity, not a single-portal demo. [query]
​

Business (30%): TAM jumps from India's ~$500B to the $13T global government procurement market — SAM.gov alone awards $700B+/yr; World Bank $50B+/yr. Every SMB, consultancy, NGO, and contractor worldwide is your customer.

Demo (20%): Live run showing TenderBot finding the same company a matching tender on SAM.gov AND UNGM AND TED simultaneously = jaw-dropping. [query]

What Changes in the Build
Add language detection (EU TED is multilingual) → Fireworks.ai translates tender summaries to English. [query]

Add country/portal selector in UI (user picks which portals to monitor). [query]

Store portal credentials per user per region in MongoDB (encrypted).
​

Composio pushes deadline alerts via Slack/email regardless of timezone. [query]