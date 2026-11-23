import { useId } from 'react'

interface Props {
  etiqueta: string
  valor: number
  minimo: number
  maximo: number
  paso: number
  onCambio: (v: number) => void
  formato: (v: number) => string
  ayuda?: string
}

export function Deslizador({ etiqueta, valor, minimo, maximo, paso, onCambio, formato, ayuda }: Props) {
  const id = useId()
  return (
    <div className="control">
      <div className="control__fila">
        <label htmlFor={id}>{etiqueta}</label>
        <output htmlFor={id}>{formato(valor)}</output>
      </div>
      <input id={id} type="range" min={minimo} max={maximo} step={paso} value={valor} onChange={(e) => onCambio(Number(e.target.value))} />
      {ayuda && <small>{ayuda}</small>}
    </div>
  )
}
