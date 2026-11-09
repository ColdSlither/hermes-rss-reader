"""Tool schemas — what the LLM sees."""

RSS_LIST_FEEDS = {
    "name": "rss_list_feeds",
    "description": (
        "List the RSS/Atom feeds the user is subscribed to, with names and URLs."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

RSS_ADD_FEED = {
    "name": "rss_add_feed",
    "description": (
        "Subscribe to an RSS/Atom feed by URL, with an optional display name. "
        "The first check of a new feed establishes a baseline silently."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "RSS/Atom feed URL to subscribe to",
            },
            "name": {
                "type": "string",
                "description": "Display name (defaults to the feed's own title)",
            },
        },
        "required": ["url"],
    },
}

RSS_REMOVE_FEED = {
    "name": "rss_remove_feed",
    "description": (
        "Unsubscribe from an RSS/Atom feed by URL. Also forgets its seen-item state."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "RSS/Atom feed URL to remove",
            },
        },
        "required": ["url"],
    },
}

RSS_FETCH = {
    "name": "rss_fetch",
    "description": (
        "Fetch any RSS/Atom feed URL and return its items (title, link, date). "
        "One-shot read with no state changes — use rss_check for new-item watching."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "RSS/Atom feed URL to fetch",
            },
            "max_items": {
                "type": "integer",
                "description": "Maximum items to return (1-100, default 20)",
            },
        },
        "required": ["url"],
    },
}

RSS_CHECK = {
    "name": "rss_check",
    "description": (
        "Check subscribed feeds for NEW items since the last check and update the "
        "seen state. Omit url to check every subscribed feed. A feed's first check "
        "establishes a baseline (marked seen, reported under baselined, NOT as new) "
        "so watchers never flood on setup. Prefer this over rss_fetch for monitoring."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Single subscribed feed URL to check (omit for all feeds)",
            },
        },
    },
}
