import { useRef, useState } from 'react'

interface Props {
  titulo: string
  ayuda: string
  multiple?: boolean
  onArchivos: (archivos: File[]) => void
  onCamara?: () => void
  ejemplos?: string[]
  onEjemplo?: (id: string) => void
}

/** Zona para soltar o elegir fotos, con cámara y fotos de ejemplo opcionales. */
export function Zona({ titulo, ayuda, multiple = false, onArchivos, onCamara, ejemplos, onEjemplo }: Props) {
  const entrada = useRef<HTMLInputElement>(null)
  const [activa, setActiva] = useState(false)

  const recibir = (lista: FileList | null) => {
    if (!lista) return
    const imagenes = Array.from(lista).filter((f) => f.type.startsWith('image/'))
    if (imagenes.length) onArchivos(multiple ? imagenes : imagenes.slice(0, 1))
  }

  return (
    <div
      className={`zona${activa ? ' zona--activa' : ''}`}
      onDragOver={(e) => {
        e.preventDefault()
        setActiva(true)
      }}
      onDragLeave={() => setActiva(false)}
      onDrop={(e) => {
        e.preventDefault()
        setActiva(false)
        recibir(e.dataTransfer.files)
      }}
    >
      <h2 className="titulo">{titulo}</h2>
      <p>{ayuda}</p>
      <div className="zona__botones">
        <button type="button" className="boton boton--primario" onClick={() => entrada.current?.click()}>
          {multiple ? 'Elegir fotos' : 'Elegir una foto'}
        </button>
        {onCamara && (
          <button type="button" className="boton" onClick={onCamara}>
            Usar la cámara
          </button>
        )}
      </div>
      <input ref={entrada} type="file" accept="image/*" multiple={multiple} onChange={(e) => { recibir(e.target.files); e.target.value = '' }} />
      {ejemplos && onEjemplo && (
        <div className="ejemplos">
          <span>O pruebe con una foto de ejemplo</span>
          {ejemplos.map((id, i) => (
            <button key={id} type="button" className="ejemplo" onClick={() => onEjemplo(id)}>
              <img src={`/ejemplos/ejemplo-${id}.jpg`} alt="" />
              Ejemplo {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
