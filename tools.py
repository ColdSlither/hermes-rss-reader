"""Agent tool handlers — always return a JSON string, never raise."""

import json

if __package__:
    from . import feeds as _core
else:  # standalone load (desktop backend via file path, smoke tests)
    import feeds as _core


def _ok(**fields) -> str:
    return json.dumps({"success": True, **fields})


def _err(message: str) -> str:
    return json.dumps({"success": False, "error": message})


def rss_list_feeds(args: dict, **kwargs) -> str:
    try:
        state = _core.load_state()
        return _ok(feeds=state["feeds"], count=len(state["feeds"]))
    except Exception as exc:
        return _err(f"Could not list feeds: {exc}")


def rss_add_feed(args: dict, **kwargs) -> str:
    url = (args.get("url") or "").strip()
    if not url.lower().startswith(("http://", "https://")):
        return _err("url must be an http(s) feed URL")
    try:
        state = _core.load_state()
        if any(f.get("url") == url for f in state["feeds"]):
            return _ok(feeds=state["feeds"], note="Already subscribed")
        name = (args.get("name") or "").strip()
        if not name:
            try:
                items = _core.parse_feed(_core.fetch_text(url))
                _ = items  # fetch validates; name comes from state default below
            except Exception:
                pass
            name = url.split("//", 1)[-1].split("/", 1)[0]
        state["feeds"].append({"name": name, "url": url})
        _core.save_state(state)
        return _ok(feeds=state["feeds"], note=f"Subscribed to {name}")
    except Exception as exc:
        return _err(f"Could not add feed: {exc}")


def rss_remove_feed(args: dict, **kwargs) -> str:
    url = (args.get("url") or "").strip()
    try:
        state = _core.load_state()
        before = len(state["feeds"])
        state["feeds"] = [f for f in state["feeds"] if f.get("url") != url]
        state.get("seen", {}).pop(url, None)
        _core.save_state(state)
        removed = before - len(state["feeds"])
        return _ok(feeds=state["feeds"], note="Removed" if removed else "Was not subscribed")
    except Exception as exc:
        return _err(f"Could not remove feed: {exc}")


def rss_fetch(args: dict, **kwargs) -> str:
    url = (args.get("url") or "").strip()
    if not url.lower().startswith(("http://", "https://")):
        return _err("url must be an http(s) feed URL")
    try:
        max_items = int(args.get("max_items", 20))
    except (TypeError, ValueError):
        max_items = 20
    try:
        result = _core.fetch_feed(url, max_items=max_items)
        return _ok(**result)
    except Exception as exc:
        return _err(f"Could not fetch {url}: {type(exc).__name__}: {exc}")


def rss_check(args: dict, **kwargs) -> str:
    url = (args.get("url") or "").strip() or None
    try:
        state = _core.load_state()
        if url and not any(f.get("url") == url for f in state["feeds"]):
            return _err(f"Not subscribed: {url}. Use rss_add_feed first.")
        if url:
            result = _core.check_feed(url, state)
            _core.save_state(state)
            return _ok(checked=[result], errors={})
        result = _core.check_all(state)
        _core.save_state(state)
        return _ok(checked=result["results"], errors=result["errors"])
    except Exception as exc:
        return _err(f"Check failed: {exc}")
