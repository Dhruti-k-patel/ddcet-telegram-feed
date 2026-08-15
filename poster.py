"""Posts messages to the Telegram channel via the Bot API."""

import html
import time

import requests

from config import (
    DRY_RUN,
    REQUEST_TIMEOUT,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
)

API = "https://api.telegram.org/bot{token}/sendMessage"

SOURCE_TAG = {"GTU": "#GTU", "ACPC": "#ACPC"}


def format_message(item, summary):
    """Build an HTML-formatted Telegram message for one notice."""
    tag = SOURCE_TAG.get(item["source"], f"#{item['source']}")
    title = html.escape(item["title"])
    lines = [f"<b>{tag} · DDCET Update</b>", "", title]
    if summary:
        lines += ["", html.escape(summary)]
    if item["url"]:
        lines += ["", f'<a href="{html.escape(item["url"])}">🔗 Open notice</a>']
    lines += ["", "#DDCET #DiplomaToDegree"]
    return "\n".join(lines)


def send(text):
    """Send one message. Returns True on success."""
    if DRY_RUN:
        print("  [dry-run] would post:\n" + "\n".join("    " + l for l in text.splitlines()))
        return True

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("  [error] TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID not set.")
        return False

    url = API.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, data=payload, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        if not data.get("ok"):
            print(f"  [error] telegram: {data.get('description')}")
            return False
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  [error] telegram request failed: {exc}")
        return False


def post_items(items_with_summaries):
    """
    Post a list of (item, summary) tuples, pacing to respect rate limits.

    Returns the list of items that were posted successfully, so the caller can
    mark only those as seen (failed posts should be retried on the next run).
    """
    posted_items = []
    for item, summary in items_with_summaries:
        text = format_message(item, summary)
        if send(text):
            posted_items.append(item)
            print(f"  posted: {item['title'][:70]}")
            time.sleep(3)  # stay well under Telegram's ~20 msg/min channel limit
    return posted_items
