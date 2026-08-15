"""
Configuration for the DDCET Telegram news feed.

Secrets (bot token, channel id) come from environment variables so they are
never committed to git. Everything else you can tune right here.
"""

import os

# ---------------------------------------------------------------------------
# Secrets (set as environment variables locally, or as GitHub Actions secrets)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# Channel id: either "@yourchannelusername" (public) or a numeric "-100..." id
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Optional: Anthropic API key. If present, notices are summarised by Claude.
# If empty, a free rule-based summary is used instead (no cost, no key needed).
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
# Each source is scraped by a dedicated function in sources.py.
SOURCES = {
    # ACPC is the primary source: the DDCET / diploma-to-degree pages carry all
    # the exam & admission notices (answer keys, key dates, seat matrix, etc.).
    "ACPC": {
        "name": "ACPC",
        "urls": [
            "https://gujacpc.admissions.nic.in/ddcet/",
            "https://gujacpc.admissions.nic.in/diploma-to-degree/",
            "https://gujacpc.admissions.nic.in/",
        ],
        "base": "https://gujacpc.admissions.nic.in/",
    },
    # GTU rarely posts DDCET-specific content (DDCET is run by ACPC), but we keep
    # it configured with tight filtering so anything DDCET-related is still caught.
    "GTU": {
        "name": "GTU",
        "urls": [
            "https://www.gtu.ac.in/",
        ],
        "base": "https://www.gtu.ac.in/",
    },
}

# Hosts/paths that indicate a real document/notice link (vs a nav menu link).
# NOTE: deliberately NOT "admissions.nic.in" — the whole ACPC site is on that
# host, so it would let every menu link through.
DOCUMENT_HOST_HINTS = [
    ".pdf", "cdnbbsr.s3waas.gov.in", "s3waas.gov.in", "gtusitecirculars",
    "s3-ap-southeast",
]

# href fragments that mark a navigation/menu link to ignore.
NAV_HREF_HINTS = ["page.aspx", "javascript:", "mailto:", "tel:", "#"]

# ---------------------------------------------------------------------------
# Relevance filter
# ---------------------------------------------------------------------------
# A notice is posted only if its text contains at least one INCLUDE keyword.
# Keep this focused on DDCET / diploma-to-degree engineering admission news.
INCLUDE_KEYWORDS = [
    "ddcet", "d2d", "d to d", "diploma to degree", "diploma-to-degree",
    "diploma to degree engineering", "degree engineering",
    "d2d admission", "ddcet exam", "ddcet result", "ddcet answer key",
    "common entrance test", "entrance test",
    "acpc", "admission", "merit list", "provisional merit", "final merit",
    "choice filling", "mock round", "mop-up", "mopup", "seat matrix",
    "registration", "answer key", "result", "syllabus", "exam date",
    "hall ticket", "time table", "timetable", "counselling", "counseling",
]

# If a notice contains any of these AND none of the strong DDCET terms,
# it is skipped. These are the post-graduate / other-course streams that share
# the ACPC news area but are NOT relevant to a DDCET (diploma-to-degree) channel.
EXCLUDE_KEYWORDS = [
    "pgcet", "mba", "mca", "b.arch", "m.arch",
    "mtech", "m.tech", "me/mtech", "me admission", "m.e.",
    "mpharm", "m.pharm", "mplan", "m.plan",
    "ph.d", "phd", "convocation", "sports", "cultural fest",
]

# Strong terms that ALWAYS keep a notice (checked before the exclude list).
# "d to d" and "diploma to degree" cover the seat-matrix / round notices.
STRONG_KEYWORDS = [
    "ddcet", "d2d", "d to d", "diploma to degree", "diploma-to-degree",
    "degree engineering",
]

# Engineering-only mode: drop Pharmacy-specific DDCET notices. A notice is
# dropped only if it mentions pharmacy AND does NOT mention engineering, so
# combined ("DDCET Engineering and Pharmacy") and general DDCET notices stay.
ENGINEERING_ONLY = True
PHARMACY_TERMS = ["pharmacy", "m.pharm", "mpharm", "d.pharm", "b.pharm"]
ENGINEERING_TERMS = ["engineering", "b.e.", "b.tech", "b tech"]

# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# GTU: Diploma in Engineering Sem 5 & 6 notices (results, recheck, timetables).
# GTU is IP-blocked from cloud servers, so this only runs from the user's PC.
# A notice is kept if it mentions diploma engineering AND semester 5 or 6.
# ---------------------------------------------------------------------------
GTU_COURSE_TERMS = ["diploma in engineering", "diploma engineering"]
# Matches "Sem-5", "Sem 6", "Semester-5", "Semester 6", "Sem-05", etc.
GTU_SEM_PATTERN = r"sem(?:ester)?[-\s]?0?[56]\b"

# Restrict which sources are scraped this run (env var, comma-separated).
# e.g. ONLY_SOURCES=GTU (PC run) or ONLY_SOURCES=ACPC (cloud run). Empty = all.
ONLY_SOURCES = [
    s.strip().upper()
    for s in os.environ.get("ONLY_SOURCES", "").split(",")
    if s.strip()
]

# State file is env-overridable so the PC GTU run keeps its own tracking file
# (seen_gtu.json) separate from the cloud ACPC run (seen.json).
SEEN_FILE = os.environ.get("SEEN_FILE", "seen.json")
MAX_POSTS_PER_RUN = 8              # safety cap so a first run doesn't flood
REQUEST_TIMEOUT = 30              # seconds
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

# Browser-like headers — Indian gov sites reject the default requests UA.
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,gu;q=0.8",
}
