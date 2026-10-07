import type { ChatMessage, ChatResponse, Product } from './types'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    // FastAPI validation errors arrive as a list; show the first message.
    const detail = Array.isArray(body.detail)
      ? String(body.detail[0]?.msg ?? '').replace(/^Value error, /, '')
      : body.detail
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return res.json() as Promise<T>
}

export const getProducts = () => request<Product[]>('/api/products')

export const getProduct = (id: string) =>
  request<Product>(`/api/products/${encodeURIComponent(id)}`)

export interface PageContext {
  path: string
  product_id: string | null
  results_title: string | null
}

export const sendChat = (message: string, history: ChatMessage[], page: PageContext) =>
  request<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      // Only used for guests; logged-in history is loaded from the DB server-side.
      history: history.map(({ role, content }) => ({ role, content })),
      page,
    }),
  })

interface HistoryMessage {
  role: 'user' | 'assistant'
  content: string
  products: Product[]
  page_title: string | null
}

export const getChatHistory = () =>
  request<HistoryMessage[]>('/api/chat/history').then((rows) =>
    rows.map<ChatMessage>((r) => ({ role: r.role, content: r.content, products: r.products, pageTitle: r.page_title })),
  )

export const clearChatHistory = () => request<{ ok: boolean }>('/api/chat/history', { method: 'DELETE' })

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
}

export interface SignupData {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

export const authApi = {
  me: () => request<User>('/api/auth/me'),
  login: (email: string, password: string) =>
    request<User>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  signup: (data: SignupData) =>
    request<User>('/api/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),
}

export const formatPrice = (n: number) => `$${n.toFixed(2)}`
