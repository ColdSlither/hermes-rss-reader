# hermes-rss-reader

Personal RSS/Atom reader for [Hermes Agent](https://github.com/NousResearch/hermes-agent) — by ColdSlither.

- **Agent tools** (`rss` toolset): list, add, remove, fetch, and check feeds with new-item dedup
- **Desktop pane**: reader UI inside the Hermes desktop app (server-side fetching, no CORS limits)
- **Watch blueprint** (`rss-reader:watch`): weekly feed check that reports only genuinely new items
- Seeded with Phrack community feeds (`phrack-feed.lh.mk` — Phrack ships no official RSS)

## Install (pre-catalog: direct from git)

```bash
hermes plugins install git@github.com:ColdSlither/hermes-rss-reader.git
hermes plugins enable rss-reader
```

Catalog listing (`hermes plugins install rss-reader`) follows once the
`plugin-catalog/rss-reader.yaml` PR is reviewed and merged.

## Tools

| Tool | What it does |
|---|---|
| `rss_list_feeds` | List subscribed feeds |
| `rss_add_feed` | Subscribe by URL (first check baselines silently) |
| `rss_remove_feed` | Unsubscribe and forget seen state |
| `rss_fetch` | One-shot fetch of any feed URL, no state changes |
| `rss_check` | New items since last check across one/all feeds |

## Blueprint

`/blueprint rss-reader:watch` — pick a feed URL, a time, and a destination.
Runs weekly (Mondays); silent unless something lands.

## Layout

```
plugin.yaml          manifest (provides_tools drives catalog + validate)
__init__.py          register(): tools + blueprint
schemas.py           what the LLM sees
feeds.py             shared core: fetch/parse/state (stdlib only)
tools.py             handlers (always JSON out, never raise)
dashboard/           gateway API the desktop pane calls (server-side fetch)
desktop/plugin.js    reader pane + palette command (SDK only, no core patching)
```

State lives in the plugin data dir (`plugin-data/rss-reader/`), so updates
never wipe subscriptions or seen-item history.

## License

MIT — ColdSlither, 2026.
