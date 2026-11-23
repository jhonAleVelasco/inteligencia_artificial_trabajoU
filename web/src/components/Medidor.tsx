import { porcentaje } from '../lib/format'

interface Props {
  valor: number
  desde: number
  retirar: number
}

/** Barra de 0 a 100 % con las tres zonas de decisión y un indicador en el valor de la fruta. */
export function Medidor({ valor, desde, retirar }: Props) {
  const p = (x: number) => `${Math.min(Math.max(x, 0), 1) * 100}%`
  return (
    <div className="medidor" role="img" aria-label={`Probabilidad de estar podrida: ${porcentaje(valor)}. Descuento desde ${porcentaje(desde)}, retiro desde ${porcentaje(retirar)}.`}>
      <span className="medidor__valor" style={{ left: p(Math.min(Math.max(valor, 0.05), 0.95)) }}>{porcentaje(valor)}</span>
      <div className="medidor__pista">
        <i style={{ width: p(desde), background: 'var(--vender-tinte)' }} />
        <i style={{ width: p(retirar - desde), background: 'var(--descuento-tinte)' }} />
        <i style={{ flex: 1, background: 'var(--retirar-tinte)' }} />
      </div>
      <span className="medidor__pin" style={{ left: p(valor) }} />
      <span className="medidor__marca medidor__marca--izq" style={{ left: p(desde) }}>Descuento desde {porcentaje(desde)}</span>
      <span className="medidor__marca" style={{ left: p(Math.min(retirar, 0.88)) }}>Retirar desde {porcentaje(retirar)}</span>
    </div>
  )
}
