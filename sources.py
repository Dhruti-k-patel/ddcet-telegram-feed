"""
Scrapers for GTU and ACPC.

Each notice is returned as a dict:
    {
        "source": "GTU" | "ACPC",
        "title": "<notice text>",
        "url":   "<absolute link, or the page url if none>",
        "uid":   "<stable id used to detect duplicates>",
    }

The parsing is deliberately tolerant: these sites change their markup often,
so we scan for links and list rows rather than relying on brittle CSS ids.
If one URL fails, the others are still tried.
"""

import hashlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import (
    DOCUMENT_HOST_HINTS,
    HTTP_HEADERS,
    NAV_HREF_HINTS,
    REQUEST_TIMEOUT,
    SOURCES,
)

_DATE_IN_TEXT = re.compile(r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}")


def _fetch(url):
    """Return page HTML, or None on any failure."""
    try:
        resp = requests.get(
            url, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT, verify=True
        )
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.SSLError:
        # Some gov sites have broken cert chains; retry once without verify.
        try:
            resp = requests.get(
                url, headers=HTTP_HEADERS, timeout=REQUEST_TIMEOUT, verify=False
            )
            resp.raise_for_status()
            return resp.text
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] fetch failed (no-verify) {url}: {exc}")
            return None
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] fetch failed {url}: {exc}")
        return None


def _uid(source, title, url):
    raw = f"{source}|{title.strip().lower()}|{url}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _clean(text):
    return " ".join(text.split()).strip()


def _is_document_link(href):
    h = href.lower()
    return any(hint in h for hint in DOCUMENT_HOST_HINTS)


def _is_nav_link(href):
    h = href.lower()
    return any(hint in h for hint in NAV_HREF_HINTS)


def _looks_like_notice(title, href):
    """
    Decide whether an anchor is a real notice rather than a menu/nav link.

    Keep it if any of:
      - it links to a document (PDF / S3 notice host / admissions portal), OR
      - its text contains a date (e.g. "20.05.2026 Provisional Answer Key ..."), OR
      - it's a long, sentence-like announcement (>= 30 chars with a space).
    """
    if _is_document_link(href):
        return True
    if _DATE_IN_TEXT.search(title):
        return True
    if len(title) >= 30 and " " in title:
        return True
    return False


def _extract_items(html, source_name, base_url):
    """Pull notice-like anchors from a page, skipping navigation/menu links."""
    soup = BeautifulSoup(html, "lxml")
    items = []
    seen_titles = set()

    for a in soup.find_all("a"):
        title = _clean(a.get_text())
        if not (12 <= len(title) <= 400):
            continue
        if not any(c.isalpha() for c in title):
            continue

        href = a.get("href") or ""
        if not href or _is_nav_link(href):
            continue
        if not _looks_like_notice(title, href):
            continue

        url = urljoin(base_url, href)
        key = title.lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        items.append(
            {
                "source": source_name,
                "title": title,
                "url": url,
                "uid": _uid(source_name, title, url),
            }
        )

    # News-ticker entries (marquee) that are plain text, not links.
    for tag in soup.find_all(["marquee"]):
        for chunk in re.split(r"\s{2,}|\n", tag.get_text("\n")):
            title = _clean(chunk)
            if not (25 <= len(title) <= 400):
                continue
            if not _DATE_IN_TEXT.search(title) and "deadline" not in title.lower():
                continue
            key = title.lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)
            items.append(
                {
                    "source": source_name,
                    "title": title,
                    "url": base_url,
                    "uid": _uid(source_name, title, base_url),
                }
            )

    return items


def scrape_source(source_key):
    """Scrape one configured source, trying each of its URLs."""
    cfg = SOURCES[source_key]
    all_items = []
    for url in cfg["urls"]:
        print(f"  fetching {url}")
        html = _fetch(url)
        if not html:
            continue
        found = _extract_items(html, cfg["name"], cfg["base"])
        print(f"    -> {len(found)} candidate items")
        all_items.extend(found)

    # De-dup by uid across the source's pages.
    unique = {}
    for it in all_items:
        unique[it["uid"]] = it
    return list(unique.values())


def scrape_all():
    results = []
    for key in SOURCES:
        print(f"[{key}]")
        try:
            results.extend(scrape_source(key))
        except Exception as exc:  # noqa: BLE001
            print(f"  [error] {key} scrape crashed: {exc}")
    return results
