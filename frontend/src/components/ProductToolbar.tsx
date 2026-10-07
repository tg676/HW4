import { CATEGORIES, DEFAULT_FILTERS, SIZES, isFiltered, type Filters, type SortKey } from '../filters'

interface Props {
  filters: Filters
  onChange: (f: Filters) => void
  shown: number
  total: number
}

export default function ProductToolbar({ filters, onChange, shown, total }: Props) {
  const set = <K extends keyof Filters>(key: K, value: Filters[K]) => onChange({ ...filters, [key]: value })

  return (
    <div className="toolbar">
      <div className="toolbar-row">
        <input
          className="toolbar-search"
          type="search"
          placeholder="Search: hockey, Berkeley, bulldog, navy…"
          value={filters.text}
          onChange={(e) => set('text', e.target.value)}
          aria-label="Search products"
        />
        <select value={filters.size} onChange={(e) => set('size', e.target.value)} aria-label="Size in stock">
          <option value="">Any size</option>
          {SIZES.map((s) => (
            <option key={s} value={s}>
              In stock in {s}
            </option>
          ))}
        </select>
        <select value={filters.sort} onChange={(e) => set('sort', e.target.value as SortKey)} aria-label="Sort">
          <option value="featured">Sort: Featured</option>
          <option value="price-asc">Price: Low → High</option>
          <option value="price-desc">Price: High → Low</option>
          <option value="name">Name: A → Z</option>
        </select>
        <label className="toolbar-check">
          <input type="checkbox" checked={filters.inStockOnly} onChange={(e) => set('inStockOnly', e.target.checked)} />
          In stock only
        </label>
      </div>
      <div className="toolbar-row">
        <div className="chips">
          {CATEGORIES.map((c) => (
            <button
              key={c.key}
              className={`chip ${filters.category === c.key ? 'active' : ''}`}
              onClick={() => set('category', c.key)}
            >
              {c.label}
            </button>
          ))}
        </div>
        <span className="muted toolbar-count">
          Showing {shown} of {total}
          {isFiltered(filters) && (
            <button className="link-btn" onClick={() => onChange(DEFAULT_FILTERS)}>
              Reset
            </button>
          )}
        </span>
      </div>
    </div>
  )
}
