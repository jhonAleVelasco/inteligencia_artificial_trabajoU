import { useEffect, useRef, useState } from 'react'

interface Props {
  abierta: boolean
  onCerrar: () => void
  onFoto: (foto: File) => void
}

/** Ventana con la cámara del equipo para tomar una foto. */
export function Camara({ abierta, onCerrar, onFoto }: Props) {
  const dialogo = useRef<HTMLDialogElement>(null)
  const video = useRef<HTMLVideoElement>(null)
  const flujo = useRef<MediaStream | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const d = dialogo.current
    if (!d) return
    const detener = () => {
      flujo.current?.getTracks().forEach((t) => t.stop())
      flujo.current = null
    }
    if (abierta) {
      setError(null)
      if (!d.open) d.showModal()
      if (!navigator.mediaDevices?.getUserMedia) {
        setError('Este navegador no permite usar la cámara aquí. Suba una foto desde el equipo.')
      } else {
        navigator.mediaDevices
          .getUserMedia({ video: { facingMode: 'environment' } })
          .then((s) => {
            flujo.current = s
            if (video.current) video.current.srcObject = s
          })
          .catch(() => setError('No se pudo abrir la cámara. Revise el permiso del navegador o suba una foto.'))
      }
    } else if (d.open) {
      d.close()
    }
    return detener
  }, [abierta])

  const tomar = () => {
    const v = video.current
    if (!v || !v.videoWidth) return
    const lienzo = document.createElement('canvas')
    lienzo.width = v.videoWidth
    lienzo.height = v.videoHeight
    lienzo.getContext('2d')?.drawImage(v, 0, 0)
    lienzo.toBlob(
      (blob) => {
        if (blob) onFoto(new File([blob], 'camara.jpg', { type: 'image/jpeg' }))
      },
      'image/jpeg',
      0.92,
    )
  }

  return (
    <dialog ref={dialogo} className="camara" onClose={onCerrar} aria-label="Cámara">
      <div className="camara__cuerpo">
        <h2 className="titulo">Tome la foto</h2>
        {error ? <p className="aviso aviso--error">{error}</p> : <video ref={video} autoPlay playsInline muted />}
        <div className="camara__botones">
          <button type="button" className="boton" onClick={onCerrar}>Cancelar</button>
          <button type="button" className="boton boton--primario" onClick={tomar} disabled={!!error}>Tomar foto</button>
        </div>
      </div>
    </dialog>
  )
}
