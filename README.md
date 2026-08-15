# DDCET Telegram News Feed

Automatically posts **DDCET / diploma-to-degree engineering** admission news from the
**GTU** and **ACPC** websites to your Telegram channel — filtered for relevance and
summarised.

- **Channel:** [@ddcetmathswarriors](https://t.me/ddcetmathswarriors)
- **Sources:** ACPC (`gujacpc.admissions.nic.in/ddcet/` + `/diploma-to-degree/`) is the primary source — it carries all the real DDCET notices (answer keys, question papers, key dates, seat matrix). GTU (`gtu.ac.in`) is also configured but runs in **strict mode**: testing showed GTU publishes *no* DDCET content (its notice stream is unrelated result declarations), so it stays silent unless it ever posts a genuine DDCET item.
- **Filter:** **engineering-only** — only DDCET Engineering notices are posted. Pharmacy-specific notices are dropped (unless a notice covers both, e.g. a shared exam-date circular). Post-graduate streams (PGCET, ME/MTech, MBA/MCA, M.Pharm) are also filtered out. See `config.py` — set `ENGINEERING_ONLY = False` to include Pharmacy again.
- **Summary:** free rule-based (dates & deadlines) by default; optional AI summary if you add an Anthropic key
- **Runs:** on a schedule via GitHub Actions (free), or on your Windows PC via Task Scheduler
- **No duplicates:** posted notices are remembered in `seen.json`

---

## ⚠️ Important: the geoblock reality

GTU and ACPC block requests from outside India / from datacenters. When this project was
built from a US environment, GTU returned `403` and ACPC refused the connection.

- **Your PC in Gujarat can reach both sites** → local testing is guaranteed to work.
- **GitHub's servers are in the US** → they *may* be blocked.

**So do Step 3 (local test) first.** It confirms the scraper works and lets us tune it to the
real page layout. Then try GitHub Actions (Step 5). If GitHub can't reach the sites, use the
Windows Task Scheduler fallback (Step 6) — same code, no changes.

---

## Step 1 — Create the Telegram bot (2 minutes)

You already have the **channel**. You still need a **bot** to post into it.

1. In Telegram, open a chat with **@BotFather**.
2. Send `/newbot`. Give it a name (e.g. `DDCET Maths Feed`) and a username ending in `bot`
   (e.g. `ddcet_maths_feed_bot`).
3. BotFather replies with a **token** like `123456789:AAE...`. Copy it — this is your
   `TELEGRAM_BOT_TOKEN`.
4. Open **your channel → Manage → Administrators → Add Admin**, search your bot's username,
   add it, and give it permission to **Post Messages**.
5. Your `TELEGRAM_CHANNEL_ID` is:
   - `@yourchannelusername` if the channel is **public**, **or**
   - a numeric `-100…` id if it's **private** (get it by forwarding a channel post to
     **@userinfobot**, or temporarily make the channel public to grab the username).

## Step 2 — Install Python + dependencies

Install Python 3.10+ from python.org (tick "Add to PATH"), then in this folder:

```
pip install -r requirements.txt
```

## Step 3 — Test locally FIRST (dry run, no posting)

This confirms the sites are reachable from your PC and that the filter catches the right
notices — **without** posting anything.

In PowerShell, from this folder:

```powershell
$env:DRY_RUN=1
python main.py
```

You'll see the candidate notices, how many were judged relevant, and what *would* be posted.
- If you see notices from both GTU and ACPC → great, the scraper works.
- If a source shows `0 candidate items` or a fetch warning → tell me, and I'll tune the parser
  to that site's exact layout (I couldn't see it from here due to the geoblock).

## Step 4 — Do a real local post (optional check)

```powershell
$env:DRY_RUN=0
$env:TELEGRAM_BOT_TOKEN="your-token"
$env:TELEGRAM_CHANNEL_ID="@your_channel_username"
python main.py
```

Check your channel — you should see the newest few notices appear. (First run posts at most
`MAX_POSTS_PER_RUN` = 8 so it doesn't flood.)

## Step 5 — Deploy to GitHub Actions (free, runs in the cloud)

1. Create a free account at github.com and a **new repository** (Private is fine).
2. Upload this whole folder to it (drag-and-drop in the browser, or `git push`).
3. In the repo: **Settings → Secrets and variables → Actions → New repository secret**. Add:
   - `TELEGRAM_BOT_TOKEN` — your bot token
   - `TELEGRAM_CHANNEL_ID` — `@yourchannel` or the `-100…` id
   - `ANTHROPIC_API_KEY` — *(optional; leave out for free summaries)*
4. Go to the **Actions** tab → select **DDCET news feed** → **Run workflow** to test it now.
5. Open the run's log. If it posted to your channel → done, it now runs automatically twice a
   day (09:00 & 17:00 IST). If the log shows fetch `403`/timeout for the sites → GitHub is
   geoblocked; use Step 6 instead.

Change the schedule by editing the `cron:` lines in `.github/workflows/feed.yml`
(times are UTC; use https://crontab.guru).

## Step 6 — Fallback: run on your Windows PC (Task Scheduler)

Use this if GitHub can't reach the sites. Your PC in India can.

1. Edit **`run_local.bat`** — put in your bot token, channel id, and set `DRY_RUN=0`.
2. Open **Task Scheduler → Create Basic Task**:
   - Trigger: Daily (or set two triggers for morning + evening).
   - Action: **Start a program** → browse to `run_local.bat`.
   - Tick "Run whether user is logged on or not" if you want it to run in the background.
3. The feed now runs on your schedule whenever the PC is on.

---

## Tuning

- **What counts as relevant** → edit `INCLUDE_KEYWORDS` / `EXCLUDE_KEYWORDS` in `config.py`.
- **Which pages are scraped** → edit `SOURCES` in `config.py`.
- **How many posts per run** → `MAX_POSTS_PER_RUN` in `config.py`.
- **AI summaries** → add `ANTHROPIC_API_KEY` (uses Claude Haiku; small cost per notice).
  Also run `pip install anthropic`.

## Files

| File | Purpose |
|------|---------|
| `main.py` | Orchestrates a run |
| `sources.py` | Scrapes GTU + ACPC |
| `filter.py` | Relevance filter + summariser |
| `poster.py` | Sends messages to Telegram |
| `config.py` | All settings & keywords |
| `seen.json` | Remembers posted notices (don't delete) |
| `.github/workflows/feed.yml` | GitHub Actions schedule |
| `run_local.bat` | Windows Task Scheduler entry point |
