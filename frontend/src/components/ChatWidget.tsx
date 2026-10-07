import { Fragment, useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { clearChatHistory, formatPrice, getChatHistory, sendChat, type PageContext } from '../api'
import { useAuth } from '../auth'
import { ASK_EVENT } from '../askBulldog'
import { useChatResults } from '../chatResults'
import type { ChatMessage } from '../types'

const greeting = (firstName?: string): ChatMessage => ({
  role: 'assistant',
  content: firstName
    ? `Welcome back, ${firstName}! Ask me about hoodies, tees, sizes, or prices.`
    : "Hi! I'm the Campus Customs assistant. Ask me about hoodies, tees, sizes, or prices.",
})

// One-tap suggestions; product-page chips rely on page context ("this" = the item on screen).
const PRODUCT_PAGE_CHIPS = ['Is this in medium?', 'What colors does this come in?', 'Show me similar items in stock']
const BROWSE_CHIPS = ['What hoodies do you have?', 'Gifts under $50', 'Anything with a bulldog?', 'Show me quarter-zips']

/** Render **bold** from saved/agent text without allowing any HTML. */
function RichText({ text }: { text: string }) {
  return (
    <>
      {text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
        part.startsWith('**') && part.endsWith('**') ? (
          <strong key={i}>{part.slice(2, -2)}</strong>
        ) : (
          <Fragment key={i}>{part}</Fragment>
        ),
      )}
    </>
  )
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([greeting()])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const { user } = useAuth()
  const { results, setResults } = useChatResults()
  const navigate = useNavigate()
  const location = useLocation()

  // Logged in → reload saved history from the DB. Logged out / guest → fresh conversation.
  useEffect(() => {
    let cancelled = false
    if (!user) {
      setMessages([greeting()])
      return
    }
    getChatHistory()
      .then((saved) => !cancelled && setMessages([greeting(user.first_name), ...saved]))
      .catch(() => !cancelled && setMessages([greeting(user.first_name)]))
    return () => {
      cancelled = true
    }
  }, [user])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open, busy])

  // Product-page "🐾 Ask" buttons: open the panel and send their question.
  const sendRef = useRef<(q: string) => void>(() => {})
  useEffect(() => {
    const onAsk = (e: Event) => {
      setOpen(true)
      sendRef.current((e as CustomEvent<string>).detail)
    }
    window.addEventListener(ASK_EVENT, onAsk)
    return () => window.removeEventListener(ASK_EVENT, onAsk)
  }, [])

  function pageContext(): PageContext {
    const m = location.pathname.match(/^\/products\/([^/]+)$/)
    return {
      path: location.pathname,
      product_id: m ? decodeURIComponent(m[1]) : null,
      results_title: location.pathname === '/products' ? (results?.title ?? null) : null,
    }
  }

  async function send(override?: string) {
    const text = (override ?? input).trim()
    if (!text || busy) return
    if (override === undefined) setInput('')
    const history = messages.slice(1) // skip the canned greeting
    setMessages((m) => [...m, { role: 'user', content: text }])
    setBusy(true)
    try {
      const res = await sendChat(text, history, pageContext())
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: res.reply, products: res.products, pageTitle: res.page_title },
      ])
      // Search results take over the page's product grid.
      if (res.page_title && res.products.length > 0) {
        setResults({ title: res.page_title, query: text, products: res.products })
        if (location.pathname !== '/products') navigate('/products')
        window.scrollTo({ top: 0, behavior: 'smooth' })
      }
    } catch (err) {
      // Server messages are shopper-safe (e.g. the 429 rate-limit notice); otherwise a generic apology.
      const detail = err instanceof Error && !err.message.startsWith('Request failed') ? err.message : null
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: detail ?? "Sorry, I couldn't reach the shop right now. Please try again." },
      ])
    } finally {
      setBusy(false)
    }
  }

  sendRef.current = (q) => void send(q)

  if (!open) {
    return (
      <button className="chat-fab" onClick={() => setOpen(true)} aria-label="Open chat: Ask the Bulldog">
        <span className="patch">
          Y<i className="ping" />
        </span>
        <span className="label">Ask the Bulldog</span>
      </button>
    )
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-title">
          <span className="chat-avatar">Y</span>
          <span>
            <b>Ask the Bulldog</b>
            <small>Online · answers from live inventory</small>
          </span>
        </div>
        <div className="chat-header-actions">
          {user && messages.length > 1 && (
            <button
              className="chat-clear"
              title="Delete my saved chat history"
              onClick={async () => {
                if (!confirm('Delete your saved chat history?')) return
                await clearChatHistory().catch(() => {})
                setMessages([greeting(user.first_name)])
              }}
            >
              Clear
            </button>
          )}
          <button onClick={() => setOpen(false)} aria-label="Close chat">
            ×
          </button>
        </div>
      </div>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg-group ${m.role}`}>
            <div className={`msg ${m.role}`}>
              <RichText text={m.content} />
            </div>
            {m.pageTitle && m.products && m.products.length > 0 && (
              <Link to="/products" className="chat-page-note">
                🛍️ {m.products.length} {m.products.length === 1 ? 'item' : 'items'} shown on the page →
              </Link>
            )}
            {!m.pageTitle && m.products && m.products.length > 0 && (
              <div className="chat-products">
                {m.products.map((p) => (
                  <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-card">
                    <img src={p.image_url} alt={p.name} />
                    <div>
                      <strong>{p.name}</strong>
                      <span>
                        {formatPrice(p.price)} · {p.total_stock > 0 ? `${p.total_stock} in stock` : 'Sold out'}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
        {busy && (
          <div className="typing-dots msg typing" aria-label="Assistant is typing">
            <i />
            <i />
            <i />
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="quick-replies">
        {(pageContext().product_id ? PRODUCT_PAGE_CHIPS : BROWSE_CHIPS).map((q) => (
          <button key={q} className="quick-reply" disabled={busy} onClick={() => send(q)}>
            {q}
          </button>
        ))}
      </div>
      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault()
          send()
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about merch…"
          autoFocus
        />
        <button type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
