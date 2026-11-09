"""Gateway-side API for the rss-reader desktop pane (reached via ctx.rest).

Server-side fetching means the pane works with any feed — no CORS limits —
against local and remote gateways alike.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))


def _core():
    """Load the sibling feeds module by file path (dir name is not importable)."""
    try:
        import feeds as core  # noqa: F401
        return core
    except Exception:
        pass
    path = _PLUGIN_ROOT / "feeds.py"
    spec = importlib.util.spec_from_file_location("rss_reader_feeds", path)
    if spec is None or spec.loader is None:
        raise HTTPException(status_code=503, detail="rss-reader core unavailable")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        logger.exception("rss-reader: core failed to load")
        raise HTTPException(status_code=503, detail=f"core load failed: {exc}")
    return mod


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "plugin": "rss-reader", "version": "0.1.0"}


@router.get("/feeds")
async def list_feeds() -> dict[str, Any]:
    core = _core()
    state = core.load_state()
    return {"feeds": state["feeds"], "count": len(state["feeds"])}


@router.post("/feeds")
async def add_feed(payload: dict) -> dict[str, Any]:
    core = _core()
    url = str(payload.get("url", "")).strip()
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="url must be an http(s) feed URL")
    state = core.load_state()
    if any(f.get("url") == url for f in state["feeds"]):
        return {"feeds": state["feeds"], "note": "Already subscribed"}
    name = str(payload.get("name", "")).strip() or url.split("//", 1)[-1].split("/", 1)[0]
    state["feeds"].append({"name": name, "url": url})
    core.save_state(state)
    return {"feeds": state["feeds"], "note": f"Subscribed to {name}"}


@router.delete("/feeds")
async def remove_feed(url: str) -> dict[str, Any]:
    core = _core()
    state = core.load_state()
    state["feeds"] = [f for f in state["feeds"] if f.get("url") != url]
    state.get("seen", {}).pop(url, None)
    core.save_state(state)
    return {"feeds": state["feeds"]}


@router.get("/items")
async def items(url: str, max_items: int = 50) -> dict[str, Any]:
    core = _core()
    try:
        return core.fetch_feed(url, max_items=max(1, min(100, max_items)))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"fetch failed: {exc}")


@router.post("/check")
async def check(payload: Optional[dict] = None) -> dict[str, Any]:
    core = _core()
    state = core.load_state()
    url = (payload or {}).get("url")
    try:
        if url:
            result = {"results": [core.check_feed(url, state)], "errors": {}}
        else:
            result = core.check_all(state)
        core.save_state(state)
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"check failed: {exc}")
