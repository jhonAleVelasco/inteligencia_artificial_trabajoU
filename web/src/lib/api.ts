import type { Config, RespuestaVarias } from './tipos'

async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  let respuesta: Response
  try {
    respuesta = await fetch(ruta, init)
  } catch {
    throw new Error('No hay conexión con el servidor. Compruebe que la API esté en marcha.')
  }
  if (!respuesta.ok) {
    let detalle = `El servidor respondió con el error ${respuesta.status}.`
    try {
      const cuerpo = await respuesta.json()
      if (typeof cuerpo.detail === 'string') detalle = cuerpo.detail
    } catch {
      /* la respuesta no era JSON */
    }
    throw new Error(detalle)
  }
  return respuesta.json() as Promise<T>
}

export const api = {
  config: () => pedir<Config>('/api/config'),
  revisar: (foto: File, confianza: number, desde: number, retirar: number) => {
    const datos = new FormData()
    datos.append('foto', foto)
    return pedir<RespuestaVarias>(
      `/api/revisar?confianza=${confianza}&descuento_desde=${desde}&retirar_desde=${retirar}`,
      { method: 'POST', body: datos },
    )
  },
}

/** Descarga una foto de ejemplo incluida en el panel y la convierte en un File. */
export async function cargarEjemplo(n: string): Promise<File> {
  const respuesta = await fetch(`/ejemplos/ejemplo-${n}.jpg`)
  if (!respuesta.ok) throw new Error('No se pudo cargar la foto de ejemplo.')
  return new File([await respuesta.blob()], `ejemplo-${n}.jpg`, { type: 'image/jpeg' })
}
