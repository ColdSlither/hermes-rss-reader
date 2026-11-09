/**
 * rss-reader desktop pane — personal feed reader inside the Hermes app.
 * All fetching goes through the plugin's gateway backend (ctx.rest),
 * so any feed works: no CORS limits, local or remote gateway.
 * Only @hermes/plugin-sdk, react and react/jsx-runtime are imported.
 */

import { host } from '@hermes/plugin-sdk'
import { useEffect, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

const ID = 'rss-reader'

const S = {
  wrap: { display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px', fontSize: '13px', height: '100%', overflowY: 'auto' },
  title: { fontWeight: 600, fontSize: '13px' },
  sub: { fontSize: '11px', color: 'var(--ui-text-tertiary)' },
  chips: { display: 'flex', gap: '6px', flexWrap: 'wrap' },
  chip: { fontSize: '11px', padding: '3px 10px', borderRadius: '999px', border: '1px solid var(--ui-stroke-secondary)', cursor: 'pointer', background: 'transparent', color: 'inherit' },
  chipOn: { borderColor: 'var(--ui-accent)', color: 'var(--ui-accent)' },
  row: { display: 'flex', gap: '6px' },
  input: { flex: 1, minWidth: 0, fontSize: '12px', padding: '6px 9px', borderRadius: '8px', border: '1px solid var(--ui-stroke-secondary)', background: 'transparent', color: 'inherit' },
  btn: { fontSize: '12px', padding: '6px 10px', borderRadius: '8px', border: '1px solid var(--ui-stroke-secondary)', background: 'transparent', color: 'inherit', cursor: 'pointer' },
  item: { border: '1px solid var(--ui-stroke-secondary)', borderRadius: '10px', padding: '8px 10px' },
  itemTitle: { fontSize: '12.5px', margin: '0 0 2px 0', cursor: 'pointer' },
  meta: { fontSize: '10.5px', color: 'var(--ui-text-tertiary)' },
  err: { fontSize: '11.5px', color: 'var(--ui-negative, #e5484d)' },
}

function ReaderPane({ api, open }) {
  const [feeds, setFeeds] = useState([])
  const [sel, setSel] = useState('')
  const [items, setItems] = useState([])
  const [filter, setFilter] = useState('')
  const [newUrl, setNewUrl] = useState('')
  const [pending, setPending] = useState(false)
  const [err, setErr] = useState('')

  const loadFeeds = async () => {
    setErr('')
    try {
      const r = await api.get('/feeds')
      setFeeds(r.feeds || [])
      if (!sel && r.feeds && r.feeds.length) setSel(r.feeds[0].url)
    } catch (e) { setErr('Could not load feeds: ' + (e.message || e)) }
  }

  const loadItems = async (url) => {
    if (!url) return
    setPending(true)
    setErr('')
    try {
      const r = await api.get('/items?url=' + encodeURIComponent(url) + '&max_items=60')
      setItems(r.items || [])
    } catch (e) { setErr('Could not fetch feed: ' + (e.message || e)); setItems([]) }
    setPending(false)
  }

  useEffect(() => { loadFeeds() }, [])
  useEffect(() => { if (sel) loadItems(sel) }, [sel])

  const q = filter.toLowerCase()
  const shown = items.filter((it) => !q || ((it.title || '') + ' ' + (it.feed || '')).toLowerCase().includes(q))

  return jsxs('div', {
    style: S.wrap,
    children: [
      jsx('div', { style: S.title, children: 'RSS Reader' }),
      jsx('div', { style: S.sub, children: feeds.length + ' feeds · ' + shown.length + ' items' }),
      jsx('div', {
        style: S.chips,
        children: feeds.map((f) => jsx('button', {
          style: Object.assign({}, S.chip, f.url === sel ? S.chipOn : null),
          onClick: () => setSel(f.url),
          title: f.url,
          children: f.name,
        }, f.url)),
      }),
      jsxs('div', {
        style: S.row,
        children: [
          jsx('input', { style: S.input, value: newUrl, placeholder: 'Add feed URL…', onChange: (e) => setNewUrl(e.target.value) }),
          jsx('button', {
            style: S.btn,
            onClick: async () => {
              if (!newUrl.trim()) return
              setPending(true)
              try {
                const r = await api.post('/feeds', { url: newUrl.trim() })
                setFeeds(r.feeds || [])
                setNewUrl('')
                const added = (r.feeds || []).find((f) => f.url === newUrl.trim())
                if (added) setSel(added.url)
              } catch (e) { setErr('Could not add feed: ' + (e.message || e)) }
              setPending(false)
            },
            children: 'Add',
          }),
          jsx('button', { style: S.btn, onClick: () => loadItems(sel), children: pending ? '…' : 'Refresh' }),
        ],
      }),
      jsx('input', { style: S.input, value: filter, placeholder: 'Filter…', onChange: (e) => setFilter(e.target.value) }),
      err ? jsx('div', { style: S.err, children: err }) : null,
      jsxs('div', {
        style: { display: 'flex', flexDirection: 'column', gap: '6px' },
        children: shown.map((it, i) => jsxs('div', {
          style: S.item,
          children: [
            jsx('p', { style: S.itemTitle, onClick: () => open(it.link), children: it.title }),
            jsx('div', { style: S.meta, children: (it.date || '') + (it.feed ? ' · ' + it.feed : '') }),
          ],
        }, (it.guid || it.link || String(i)) + i)),
      }),
    ],
  })
}

export default {
  id: ID, // must match the folder/plugin name
  name: 'RSS Reader',
  register(ctx) {
    const api = {
      get: (path) => ctx.rest(path),
      post: (path, body) => ctx.rest(path, { method: 'POST', body }),
    }
    const open = (url) => {
      if (!url) return
      try {
        const r = ctx.os && ctx.os.openExternal ? ctx.os.openExternal(url) : null
        if (r && typeof r.then === 'function') {
          r.then((ok) => { if (!ok) window.open(url, '_blank', 'noopener') })
          return
        }
        if (!r) window.open(url, '_blank', 'noopener')
      } catch (e) { window.open(url, '_blank', 'noopener') }
    }

    ctx.register({
      id: 'pane',
      area: 'panes',
      title: 'RSS Reader',
      data: { placement: 'right', width: '340px' },
      render: () => jsx(ReaderPane, { api, open }),
    })

    ctx.register({
      id: 'refresh',
      area: 'PALETTE_AREA',
      data: { title: 'RSS Reader: check all feeds for new items' },
      render: () => null,
      run: async () => {
        try {
          const r = await ctx.rest('/check', { method: 'POST', body: {} })
          const fresh = (r.results || []).reduce((n, x) => n + (x.new || []).length, 0)
          host.notify({ kind: fresh ? 'info' : 'success', message: fresh ? fresh + ' new item(s) across feeds' : 'No new items' })
        } catch (e) { host.notify({ kind: 'error', message: 'Feed check failed: ' + (e.message || e) }) }
      },
    })
  },
}
