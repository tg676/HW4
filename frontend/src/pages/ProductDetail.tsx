import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { formatPrice, getProduct } from '../api'
import { useChatResults } from '../chatResults'
import { askBulldog } from '../askBulldog'
import type { Product } from '../types'

export default function ProductDetail() {
  const { id = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState('')
  const { results } = useChatResults()

  useEffect(() => {
    setProduct(null)
    setError('')
    getProduct(id).then(setProduct).catch((e) => setError(e.message))
  }, [id])

  if (error) return <p className="page error">{error}</p>
  if (!product) return <p className="page">Loading…</p>

  return (
    <div className="page">
      <Link to="/products" className="back">
        ← Back to {results ? `“${results.title}”` : 'all products'}
      </Link>
      <div className="detail">
        <div className="detail-media">
          <span className="hangtag">{formatPrice(product.price)}</span>
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="detail-info">
          <span className="card-type">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <p className="price big">{formatPrice(product.price)}</p>
          <p>{product.description}</p>
          <div className="colors">
            {product.colors.map((c) => (
              <span key={c} className="color">
                {c}
              </span>
            ))}
          </div>

          <h3>Sizes &amp; Stock</h3>
          <div className="sizes">
            {product.inventory.map((s) => (
              <div key={s.size} className={`size ${s.quantity === 0 ? 'out' : s.quantity <= 3 ? 'low' : ''}`}>
                <strong>{s.size}</strong>
                <span>{s.quantity === 0 ? 'Sold out' : s.quantity <= 3 ? `Only ${s.quantity}!` : `${s.quantity} left`}</span>
              </div>
            ))}
          </div>
          <p className="muted">
            {product.total_stock === 0 ? 'Currently sold out in all sizes.' : `${product.total_stock} in stock across all sizes.`}
          </p>

          {/* One tap hands the question to the chat assistant, which knows which item "this" is. */}
          <div className="ask-row">
            {['Is this in medium?', 'Show me similar items in stock', 'What would go well with this?'].map((q) => (
              <button key={q} className="ask-btn" onClick={() => askBulldog(q)}>
                🐾 {q}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
