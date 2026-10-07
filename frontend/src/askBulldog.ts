/** Open the chat panel and send a question from anywhere on the site (e.g. product-page buttons). */
export const ASK_EVENT = 'cc-ask-bulldog'

export function askBulldog(question: string) {
  window.dispatchEvent(new CustomEvent<string>(ASK_EVENT, { detail: question }))
}
