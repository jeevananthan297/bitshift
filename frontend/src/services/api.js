const BASE = import.meta.env.VITE_API_BASE_URL || 'https://splitflow-phar.onrender.com/api'
export async function api(path, options = {}) {
  const config = { ...options, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) } }
  const response = await fetch(`${BASE}${path}`, config)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try { const data = await response.json(); message = data.detail || message } catch {}
    throw new Error(message)
  }
  if (response.status === 204) return null
  const type = response.headers.get('content-type') || ''
  return type.includes('application/json') ? response.json() : response.text()
}
export const get = path => api(path)
export const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) })
export const put = (path, body) => api(path, { method: 'PUT', body: JSON.stringify(body) })
export const del = path => api(path, { method: 'DELETE' })
export const money = value => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value || 0)
