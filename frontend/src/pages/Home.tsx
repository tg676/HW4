import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProducts } from '../api'
import { garmentFamily } from '../filters'
import type { Product } from '../types'

// Hand-picked hero items (real catalog ids) shown as taped-up polaroids.
const HERO_IDS = ['basic-hoodie-big-yale', '2025-yale-vs-harvard-t-shirt', 'district-vit-hoodie-vintage-bulldog']
const HERO_CAPTIONS = ['the classic', 'beat harvard', 'good boy']

const CATEGORIES = [
  { key: 'hoodie', label: 'Hoodies', icon: '🧥' },
  { key: 'crewneck', label: 'Crewnecks', icon: '🏛️' },
  { key: 'tee', label: 'T-Shirts', icon: '👕' },
  { key: 'quarter-zip', label: 'Quarter-Zips', icon: '🎓' },
  { key: 'jacket', label: 'Jackets & Fleece', icon: '❄️' },
]

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])

  useEffect(() => {
    getProducts().then(setProducts).catch(() => setProducts([]))
  }, [])

  const hero = HERO_IDS.map((id) => products.find((p) => p.product_id === id)).filter(Boolean) as Product[]
  const counts = (key: string) => products.filter((p) => garmentFamily(p.garment_type) === key).length
  const inStock = products.filter((p) => p.total_stock > 0).length

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div>
            <span className="kicker">for every Bulldog, near &amp; far</span>
            <h1>
              Bleed Blue.
              <br />
              Wear It <em>Loud.</em>
            </h1>
            <p>
              Hoodies, crewnecks, and tees for every Bulldog. Cheer at The Game, cram in Sterling, or show off your
              kid's college from three states away.
            </p>
            <div className="hero-ctas">
              <Link to="/products" className="btn cream">
                Shop the Collection
              </Link>
              <Link to="/products?cat=hoodie" className="btn ghost">
                Hoodie Season →
              </Link>
            </div>
            {products.length > 0 && (
              <div className="hero-stats">
                <span>
                  <b>{products.length}</b>styles
                </span>
                <span>
                  <b>{inStock}</b>in stock now
                </span>
                <span>
                  <b>XS–XXL</b>sizes
                </span>
              </div>
            )}
          </div>
          <div className="collage" aria-hidden={hero.length === 0}>
            {hero.map((p, i) => (
              <Link key={p.product_id} to={`/products/${p.product_id}`} className="polaroid">
                <img src={p.image_url} alt={p.name} />
                <span>{HERO_CAPTIONS[i]}</span>
              </Link>
            ))}
            <div className="pennant">YALE</div>
          </div>
        </div>
      </section>

      <section className="page">
        <span className="kicker">pick your layer</span>
        <h2 className="section-title">Shop by Category</h2>
        <div className="cats">
          {CATEGORIES.map((c) => (
            <Link key={c.key} to={`/products?cat=${c.key}`} className="cat">
              <span className="cat-icon">{c.icon}</span>
              <b>{c.label}</b>
              <small>{products.length ? `${counts(c.key)} styles` : ' '}</small>
            </Link>
          ))}
        </div>
      </section>

      <section className="page tiles" style={{ paddingTop: 0 }}>
        <div className="tile">
          <h2>Big Pride, Bigger Letters</h2>
          <p>Our arched "Big Yale" sweatshirts are the campus classic. Bold, soft, and made to be lived in.</p>
        </div>
        <div className="tile">
          <h2>Your College, Your Colors</h2>
          <p>Rep Berkeley, Branford, Benjamin Franklin, and the rest of the residential college family.</p>
        </div>
        <div className="tile">
          <h2>Game Day Ready</h2>
          <p>From hockey to sailing to fencing, gear up for whichever Bulldog squad you root for.</p>
        </div>
        <div className="tile">
          <h2>Gifts for the Whole Family</h2>
          <p>Proud parent? Doting grandparent? Find something blue for everyone on your list.</p>
        </div>
      </section>

      <section className="page" style={{ paddingTop: 0 }}>
        <div className="visit">
          <div className="badge-big">
            57
            <br />
            BROADWAY
            <br />
            NEW HAVEN
          </div>
          <div>
            <span className="kicker">come say hi</span>
            <h2>Stop By the Shop</h2>
            <p>
              Find us at 57 Broadway in New Haven, a short walk from Old Campus. Can't make it? Tap the Bulldog
              patch in the corner. Our assistant checks live sizes and stock for you.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}
