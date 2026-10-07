import type { Product } from './types'

export const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL'] as const

export const CATEGORIES = [
  { key: 'all', label: 'All' },
  { key: 'hoodie', label: 'Hoodies' },
  { key: 'crewneck', label: 'Crewnecks' },
  { key: 'tee', label: 'T-Shirts' },
  { key: 'quarter-zip', label: 'Quarter-Zips' },
  { key: 'jacket', label: 'Jackets & Fleece' },
] as const

export type SortKey = 'featured' | 'price-asc' | 'price-desc' | 'name'

export interface Filters {
  text: string
  category: string
  size: string // '' = any
  inStockOnly: boolean
  sort: SortKey
}

export const DEFAULT_FILTERS: Filters = { text: '', category: 'all', size: '', inStockOnly: false, sort: 'featured' }

/** Same grouping as backend tools.garment_family: the DB has 22 garment_type spellings. */
export function garmentFamily(garmentType: string): string {
  const g = garmentType.toLowerCase()
  if (g.includes('hood')) return 'hoodie'
  if (g.includes('quarter') || g.includes('1/4')) return 'quarter-zip'
  if (g.includes('jacket') || g.includes('fleece')) return 'jacket'
  if (g.includes('crew') || g.includes('sweatshirt') || g.includes('mockneck')) return 'crewneck'
  if (g.includes('shirt') || g.includes('tee')) return 'tee'
  return 'other'
}

export function applyFilters(products: Product[], f: Filters): Product[] {
  const words = f.text.toLowerCase().split(/\s+/).filter(Boolean)
  const out = products.filter((p) => {
    if (f.category !== 'all' && garmentFamily(p.garment_type) !== f.category) return false
    if (f.inStockOnly && p.total_stock === 0) return false
    if (f.size && !p.inventory.some((s) => s.size === f.size && s.quantity > 0)) return false
    if (words.length) {
      const hay = [p.name, p.description, p.garment_type, ...p.colors, ...p.search_tags].join(' ').toLowerCase()
      if (!words.every((w) => hay.includes(w))) return false
    }
    return true
  })
  if (f.sort === 'price-asc') out.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
  if (f.sort === 'price-desc') out.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
  if (f.sort === 'name') out.sort((a, b) => a.name.localeCompare(b.name))
  return out
}

export const isFiltered = (f: Filters) =>
  f.text !== '' || f.category !== 'all' || f.size !== '' || f.inStockOnly || f.sort !== 'featured'
