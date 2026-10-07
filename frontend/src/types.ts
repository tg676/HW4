export interface SizeStock {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  image_url: string
  price: number
  inventory: SizeStock[]
  total_stock: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
  pageTitle?: string | null
}

/** POST /api/chat response — mirrors backend models.ChatResponse. */
export interface ChatResponse {
  reply: string
  products: Product[]
  /** Set when the agent ran a catalog search: show `products` as the page grid under this heading. */
  page_title: string | null
}
