import { createContext, useContext, useState, type ReactNode } from 'react'
import type { Product } from './types'

/** Search results the chat agent put on the page (survives navigating to a detail page and back). */
export interface ChatResults {
  title: string
  query: string
  products: Product[]
}

interface ChatResultsState {
  results: ChatResults | null
  setResults: (r: ChatResults | null) => void
}

const Ctx = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)
  return <Ctx.Provider value={{ results, setResults }}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useChatResults() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useChatResults must be used inside ChatResultsProvider')
  return ctx
}
