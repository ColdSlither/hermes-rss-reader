"""rss-reader — personal RSS/Atom reader: agent tools, desktop pane, watch blueprint."""

from . import schemas, tools


def register(ctx):
    """Wire schemas to handlers, then add the watch blueprint."""
    ctx.register_tool(name="rss_list_feeds", toolset="rss",
                      schema=schemas.RSS_LIST_FEEDS, handler=tools.rss_list_feeds)
    ctx.register_tool(name="rss_add_feed", toolset="rss",
                      schema=schemas.RSS_ADD_FEED, handler=tools.rss_add_feed)
    ctx.register_tool(name="rss_remove_feed", toolset="rss",
                      schema=schemas.RSS_REMOVE_FEED, handler=tools.rss_remove_feed)
    ctx.register_tool(name="rss_fetch", toolset="rss",
                      schema=schemas.RSS_FETCH, handler=tools.rss_fetch)
    ctx.register_tool(name="rss_check", toolset="rss",
                      schema=schemas.RSS_CHECK, handler=tools.rss_check)

    ctx.register_automation_blueprint(
        "watch",
        title="RSS feed watch",
        description="Watch an RSS/Atom feed and report only genuinely new items. Deduped against what was already seen, so repeat runs stay silent unless something lands.",
        schedule_template="{minute} {hour} * * 1",
        prompt_template=(
            "Using the rss-reader plugin's rss_check tool, check the RSS/Atom feed "
            "at {url} for new items. Report only genuinely new items with title and "
            "link. If there is nothing new, say so briefly and stop."
        ),
        slots=[
            {"name": "url", "type": "text", "label": "Which feed URL?",
             "default": "https://phrack-feed.lh.mk/issues.xml"},
            {"name": "time", "type": "time", "label": "What time?", "default": "09:00"},
            {"name": "deliver", "type": "enum", "label": "Where to deliver?",
             "default": "origin", "options": ["origin", "local"], "strict": False},
        ],
        tags=["rss", "watch"],
    )
