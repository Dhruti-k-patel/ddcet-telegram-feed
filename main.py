"""
DDCET Telegram news feed — entry point.

Flow:
  1. Scrape GTU + ACPC.
  2. Keep only DDCET / diploma-to-degree relevant notices.
  3. Drop anything already posted (tracked in seen.json).
  4. Summarise and post the new ones to the Telegram channel.
  5. Save the updated seen.json.

Run locally:
    DRY_RUN=1 python main.py      # scrape + filter, print but don't post
    python main.py                # for real (needs env vars set)
"""

import json
import os
import sys

# Ensure emoji / Gujarati text print correctly on the Windows console.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from config import DRY_RUN, MAX_POSTS_PER_RUN, SEEN_FILE
from filter import keep_item, summarise
from poster import post_items
from sources import scrape_all


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as fh:
            return set(json.load(fh))
    except Exception:  # noqa: BLE001
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as fh:
        json.dump(sorted(seen), fh, ensure_ascii=False, indent=0)


def main():
    print("=== DDCET feed run ===")
    seen = load_seen()
    first_run = len(seen) == 0

    scraped = scrape_all()
    print(f"\nTotal candidates: {len(scraped)}")

    relevant = [it for it in scraped if keep_item(it)]
    print(f"Relevant to DDCET: {len(relevant)}")

    fresh = [it for it in relevant if it["uid"] not in seen]
    print(f"New (not seen before): {len(fresh)}")

    # On the very first run, don't flood the channel with the whole backlog.
    # Mark everything as seen, post only the newest few.
    to_post = fresh[:MAX_POSTS_PER_RUN]
    if first_run and len(fresh) > MAX_POSTS_PER_RUN:
        print(
            f"First run: {len(fresh)} items found; posting newest "
            f"{MAX_POSTS_PER_RUN}, marking the rest as seen."
        )

    prepared = [(it, summarise(it["title"])) for it in to_post]

    print("\nPosting...")
    posted_items = post_items(prepared)
    print(f"Posted {len(posted_items)} message(s).")

    # Dry runs must NOT persist state, otherwise a later real run thinks these
    # notices were already posted and skips them.
    if DRY_RUN:
        print("Dry run: state NOT saved.")
        return

    # If we tried to post but nothing went through, treat it as a failure
    # (bad token, bot not admin, network) and DON'T poison the state — so a
    # fixed re-run will post these notices instead of skipping them.
    if to_post and not posted_items:
        print(
            "ERROR: had notices to post but none succeeded. "
            "Check the bot token and that the bot is a channel admin. "
            "State NOT saved — fix the issue and run again."
        )
        return

    posted_uids = {it["uid"] for it in posted_items}
    for it in fresh:
        if it["uid"] in posted_uids:
            seen.add(it["uid"])  # actually posted
        elif first_run and it not in to_post:
            seen.add(it["uid"])  # first-run backlog we intentionally skipped
        # else: a to_post item that failed -> leave unseen so it retries.
    save_seen(seen)
    print(f"State saved: {len(seen)} notices tracked.")


if __name__ == "__main__":
    main()
