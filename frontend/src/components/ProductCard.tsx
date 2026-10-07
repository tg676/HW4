import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'

export default function ProductCard({ product, index = 0 }: { product: Product; index?: number }) {
  const soldOut = product.total_stock === 0
  return (
    <Link
      to={`/products/${product.product_id}`}
      className="card"
      style={{ animationDelay: `${Math.min(index, 12) * 45}ms` } as CSSProperties}
    >
      <div className="card-img">
        <span className="hangtag">{formatPrice(product.price)}</span>
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {soldOut && (
          <div className="stamp">
            <span>Sold out</span>
          </div>
        )}
      </div>
      <div className="card-body">
        <span className="card-type">{product.garment_type}</span>
        <h3>{product.name}</h3>
        <p className="card-desc">{product.description}</p>
        {/* At-a-glance availability: blue = in stock, gold = 1-3 left, struck = sold out */}
        <div className="size-strip" aria-label="Sizes">
          {product.inventory.map((s) => (
            <span
              key={s.size}
              className={s.quantity === 0 ? 'out' : s.quantity <= 3 ? 'low' : ''}
              title={s.quantity === 0 ? `${s.size}: sold out` : `${s.size}: ${s.quantity} left`}
            >
              {s.size}
            </span>
          ))}
        </div>
      </div>
    </Link>
  )
}
