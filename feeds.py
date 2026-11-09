"""Shared RSS/Atom core for the rss-reader plugin (stdlib only).

Used by both the agent tools (tools.py) and the desktop backend
(dashboard/plugin_api.py), so feed handling never drifts between surfaces.

NOTE on XML parsing: xml.etree is used on feed XML only — the pinned default
feeds plus URLs the user explicitly subscribes to — not on arbitrary
untrusted documents.
"""

from __future__ import annotations

import json
import urllib.request
import xml.etree.ElementTree as ET  # safe here: feed XML only, see note above
from pathlib import Path

PLUGIN_NAME = "rss-reader"
USER_AGENT = "hermes-rss-reader/0.1.0"
FETCH_TIMEOUT = 30
MAX_SEEN_PER_FEED = 500

DEFAULT_FEEDS = [
    {"name": "Phrack — new issues", "url": "https://phrack-feed.lh.mk/issues.xml"},
    {"name": "Phrack #72 — titles", "url": "https://phrack-feed.lh.mk/titles.xml"},
]


def data_dir() -> Path:
    """Per-plugin data root (survives updates/removes, follows the profile)."""
    try:
        from plugins.plugin_storage import plugin_data_dir
        return plugin_data_dir(PLUGIN_NAME)
    except Exception:
        fallback = Path.home() / ".hermes" / "plugin-data" / PLUGIN_NAME
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _state_file() -> Path:
    return data_dir() / "state.json"


def load_state() -> dict:
    """Load {feeds: [{name, url}], seen: {url: [guid, ...]}}. Seeds defaults."""
    path = _state_file()
    if path.exists():
        try:
            state = json.loads(path.read_text())
            if isinstance(state.get("feeds"), list):
                state.setdefault("seen", {})
                return state
        except (ValueError, OSError):
            pass
    state = {"feeds": [dict(f) for f in DEFAULT_FEEDS], "seen": {}}
    save_state(state)
    return state


def save_state(state: dict) -> None:
    path = _state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def fetch_text(url: str) -> str:
    """Fetch a URL as text. Raises on network/HTTP failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse_feed(xml_text: str, source: str = "") -> list:
    """Parse RSS (item) or Atom (entry) XML into item dicts. Never raises."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items = []
    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        title = link = guid = date = ""
        for child in node:
            kind = _local(child.tag)
            if kind == "title" and not title:
                title = (child.text or "").strip()
            elif kind == "link":
                if (child.text or "").strip():
                    link = child.text.strip()
                elif child.get("href"):
                    link = child.get("href").strip()
            elif kind in ("guid", "id") and not guid:
                guid = (child.text or "").strip()
            elif kind in ("pubDate", "published", "updated") and not date:
                date = (child.text or "").strip()[:10]
        guid = guid or link or title
        if title or link:
            items.append({"title": title or "(untitled)", "link": link,
                          "guid": guid, "date": date, "feed": source})
    return items


def fetch_feed(url: str, max_items: int = 20) -> dict:
    """One-shot fetch+parse of any feed URL. No state changes."""
    max_items = max(1, min(100, max_items))
    items = parse_feed(fetch_text(url), source=url)
    return {"url": url, "count": len(items), "items": items[:max_items]}


def check_feed(url: str, state: dict) -> dict:
    """Check one subscribed feed for new items; updates state in place."""
    items = parse_feed(fetch_text(url), source=url)
    seen = set(state.get("seen", {}).get(url, []))
    if not seen and items:
        # First check establishes a baseline silently — no flood on setup.
        state.setdefault("seen", {})[url] = [i["guid"] for i in items][:MAX_SEEN_PER_FEED]
        return {"url": url, "new": [], "baselined": len(items)}
    new = [i for i in items if i["guid"] not in seen]
    if new:
        merged = [i["guid"] for i in new] + sorted(seen)
        state.setdefault("seen", {})[url] = merged[:MAX_SEEN_PER_FEED]
    return {"url": url, "new": new, "baselined": 0}


def check_all(state: dict) -> dict:
    """Check every subscribed feed. Per-feed errors are reported, not raised."""
    results, errors = [], {}
    for feed in state.get("feeds", []):
        url = feed.get("url", "")
        try:
            results.append(check_feed(url, state))
        except Exception as exc:
            errors[url] = f"{type(exc).__name__}: {exc}"
    return {"results": results, "errors": errors}
