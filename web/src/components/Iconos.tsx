import type { ReactNode } from 'react'

function Icono({ children }: { children: ReactNode }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {children}
    </svg>
  )
}

export const IconoRevisar = () => (
  <Icono>
    <path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16" />
    <circle cx="12" cy="12" r="3.4" />
  </Icono>
)
export const IconoPrecios = () => (
  <Icono>
    <path d="M9 4h10.5v16H9L3.5 12z" />
    <circle cx="9" cy="12" r="1.2" />
  </Icono>
)

/** Marca: una etiqueta de precio. */
export function Marca() {
  return (
    <svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">
      <path d="M9 2h21v28H9L2 16z" fill="#12212c" />
      <circle cx="9" cy="16" r="2.6" fill="#e6ebee" />
    </svg>
  )
}
