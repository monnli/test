// 通用工具函数，按需添加。
export function formatTimestamp(ts: number | string | Date): string {
  const d = typeof ts === 'number' || typeof ts === 'string' ? new Date(ts) : ts
  const pad = (n: number) => String(n).padStart(2, '0')
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  )
}
