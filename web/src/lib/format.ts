const moneda = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

/** 1500 -> "$1.500" */
export function pesos(valor: number): string {
  return moneda.format(Math.round(valor)).replace(/\s/g, '')
}

/** 0.865 -> "87%" */
export function porcentaje(valor: number, decimales = 0): string {
  return `${(valor * 100).toFixed(decimales).replace('.', ',')}%`
}

export function fechaCorta(iso: string): string {
  const f = new Date(iso)
  return f.toLocaleString('es-CO', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
}

export function plural(n: number, uno: string, varios: string): string {
  return `${n} ${n === 1 ? uno : varios}`
}
