import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getProducts } from '../api'
import { useChatResults } from '../chatResults'
import ProductCard from '../components/ProductCard'
import ProductToolbar from '../components/ProductToolbar'
import { DEFAULT_FILTERS, applyFilters, type Filters } from '../filters'
import type { Product } from '../types'

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState('')
  const [params] = useSearchParams()
  // Home-page category tiles link here as /products?cat=hoodie
  const [filters, setFilters] = useState<Filters>(() => ({ ...DEFAULT_FILTERS, category: params.get('cat') ?? 'all' }))
  useEffect(() => {
    setFilters((f) => ({ ...f, category: params.get('cat') ?? f.category }))
  }, [params])
  const { results, setResults } = useChatResults()

  useEffect(() => {
    getProducts().then(setProducts).catch((e) => setError(e.message))
  }, [])

  // Chat search results (from the agent) replace the full catalog until cleared; the toolbar filters either.
  const base = results ? results.products : products
  const shown = useMemo(() => (base ? applyFilters(base, filters) : []), [base, filters])

  return (
    <div className="page">
      {results ? (
        <div className="chat-results-banner">
          <div>
            <span className="muted">From your chat: “{results.query}”</span>
            <h1>{results.title}</h1>
            <span className="muted">
              {results.products.length} {results.products.length === 1 ? 'match' : 'matches'}
            </span>
          </div>
          <button className="btn secondary" onClick={() => setResults(null)}>
            Show all products
          </button>
        </div>
      ) : (
        <div>
          <span className="kicker">the whole closet</span>
          <h1 className="section-title">Shop All Products</h1>
        </div>
      )}
      {error && <p className="error">{error}</p>}
      {!base && !error && <p>Loading products…</p>}
      {base && (
        <>
          <ProductToolbar filters={filters} onChange={setFilters} shown={shown.length} total={base.length} />
          {shown.length === 0 ? (
            <div className="empty">
              <p>No items match those filters.</p>
              <button className="btn secondary" onClick={() => setFilters(DEFAULT_FILTERS)}>
                Reset filters
              </button>
            </div>
          ) : (
            <div className="grid">
              {shown.map((p, i) => (
                <ProductCard key={p.product_id} product={p} index={i} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
