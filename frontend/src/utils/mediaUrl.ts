/** 将后端返回的 `/storage/...` 转为可播放的完整 URL（与 VITE_API_BASE_URL 同源，避免 MIME/404）。 */
export function resolveMediaUrl(path: string | null | undefined): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const api = import.meta.env.VITE_API_BASE_URL || '/api'
  const origin = api.replace(/\/api\/?$/, '')
  return `${origin}${path.startsWith('/') ? path : `/${path}`}`
}
