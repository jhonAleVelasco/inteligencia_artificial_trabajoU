import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, cargarEjemplo } from '../lib/api'
import { usarPanel } from '../lib/contexto'
import { accionDeFruta, resumirEscena } from '../lib/logic'
import { pesos, plural, porcentaje } from '../lib/format'
import type { Ruta } from '../lib/ruta'
import { ETIQUETA_ACCION } from '../lib/textos'
import type { RespuestaVarias } from '../lib/tipos'
import { Camara } from '../components/Camara'
import { FotoConCajas, type FrutaEvaluada } from '../components/FotoConCajas'
import { LibroFrutas } from '../components/LibroFrutas'
import { Medidor } from '../components/Medidor'
import { Ranking } from '../components/Ranking'
import { Leyenda, Regleta } from '../components/Regleta'
import { Reglas } from '../components/Reglas'
import { Zona } from '../components/Zona'

const EJEMPLOS = ['01', '03', '07']

export function Revisar({ ruta, activa }: { ruta: Ruta; activa: boolean }) {
  const { ajustes } = usarPanel()
  const [url, setUrl] = useState<string | null>(null)
  const [datos, setDatos] = useState<RespuestaVarias | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [seleccion, setSeleccion] = useState<number | null>(null)
  const [camara, setCamara] = useState(false)
  const ajustesRef = useRef(ajustes)
  ajustesRef.current = ajustes
  const peticion = useRef(0)

  const analizar = useCallback(
    async (foto: File) => {
      const mia = ++peticion.current
      setCamara(false)
      setError(null)
      setSeleccion(null)
      setCargando(true)
      setUrl((anterior) => {
        if (anterior) URL.revokeObjectURL(anterior)
        return URL.createObjectURL(foto)
      })
      setDatos(null)
      try {
        const a = ajustesRef.current
        const r = await api.revisar(foto, a.confianza, a.descuentoDesde, a.retirarDesde)
        if (mia !== peticion.current) return
        setDatos(r)
      } catch (e) {
        if (mia === peticion.current) setError((e as Error).message)
      } finally {
        if (mia === peticion.current) setCargando(false)
      }
    },
    [],
  )

  const ejemplo = useCallback(
    (id: string) => {
      cargarEjemplo(id)
        .then((f) => analizar(f))
        .catch((e: Error) => setError(e.message))
    },
    [analizar],
  )

  const pedido = ruta.params.get('ejemplo')
  useEffect(() => {
    if (activa && pedido && EJEMPLOS.includes(pedido)) ejemplo(pedido)
  }, [activa, pedido, ejemplo])

  const frutas: FrutaEvaluada[] = useMemo(
    () => (datos ? datos.frutas.map((f) => ({ ...f, accionActual: accionDeFruta(f, ajustes) })) : []),
    [datos, ajustes],
  )
  const resumen = useMemo(
    () =>
      resumirEscena(
        frutas.map((f) => ({ accion: f.accionActual, fruta: f.fruta })),
        ajustes.precios,
        ajustes.descuento,
      ),
    [frutas, ajustes.precios, ajustes.descuento],
  )
  const elegida = frutas.find((f) => f.id === seleccion) ?? null

  const vacio = !url && !cargando
  return (
    <>
      <header className="cab">
        <div>
          <h1 className="titulo">Revisar fruta</h1>
          <p>Suba la foto de una fruta o de varias, separadas sobre un fondo claro. El panel detecta cada una, dice en qué estado está y le pone precio.</p>
        </div>
        {!vacio && (
          <div className="cab__acciones">
            <button type="button" className="boton" onClick={() => setCamara(true)}>Usar la cámara</button>
            <label className="boton boton--primario">
              Analizar otra foto
              <input
                type="file"
                accept="image/*"
                hidden
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) analizar(f)
                  e.target.value = ''
                }}
              />
            </label>
          </div>
        )}
      </header>

      {error && <p className="aviso aviso--error"><b>No se pudo analizar la foto.</b> {error}</p>}

      {vacio ? (
        <Zona
          titulo="Suelte aquí la foto"
          ayuda="Puede ser una sola fruta o varias. Funciona mejor con las frutas separadas, sin tocarse, sobre una mesa o tela clara y con buena luz."
          onArchivos={(a) => analizar(a[0])}
          onCamara={() => setCamara(true)}
          ejemplos={EJEMPLOS}
          onEjemplo={ejemplo}
        />
      ) : (
        <div className="cuerpo">
          <div className="principal">
            {url && (
              <FotoConCajas
                url={url}
                frutas={frutas}
                seleccion={seleccion}
                onSeleccion={setSeleccion}
                precios={ajustes.precios}
                descuento={ajustes.descuento}
                cargando={cargando}
              />
            )}
            {datos && frutas.length === 0 && (
              <div className="aviso">
                <b>No se detectó ninguna fruta.</b> Pruebe con más luz, un fondo más liso y las frutas separadas entre sí.
              </div>
            )}
            {frutas.length > 0 && (
              <div className="bloque">
                <h2>
                  {plural(frutas.length, 'fruta detectada', 'frutas detectadas')}
                  <small>Toque una fila para ver su detalle</small>
                </h2>
                <div className="tabla-scroll">
                  <LibroFrutas
                    frutas={frutas}
                    seleccion={seleccion}
                    onSeleccion={setSeleccion}
                    precios={ajustes.precios}
                    descuento={ajustes.descuento}
                  />
                </div>
              </div>
            )}
          </div>

          <aside className="inspector" aria-label="Resumen y reglas">
            {frutas.length > 0 && (
              <div className="bloque">
                <div className="valor">
                  <span className="valor__etiqueta">Valor en venta</span>
                  <span className="valor__cifra cifra">{pesos(resumen.valorCon)}</span>
                  <span className="valor__detalle">
                    {resumen.ahorro > 0 ? (
                      <>Con descuentos se rebajan <b>{pesos(resumen.ahorro)}</b> frente a {pesos(resumen.valorSin)}.</>
                    ) : (
                      <>Ninguna fruta entra en descuento con estas reglas.</>
                    )}
                  </span>
                </div>
                <Regleta conteo={resumen.conteo} />
                <Leyenda conteo={resumen.conteo} />
              </div>
            )}

            {elegida && (
              <div className="bloque">
                <h2>Detalle de la fruta {elegida.id}</h2>
                <div className="detalle">
                  <img src={elegida.recorte} alt={`Recorte de ${elegida.nombre}`} />
                  <div>
                    <h3 className="titulo">{elegida.nombre}</h3>
                    <p>{ETIQUETA_ACCION[elegida.accionActual]}. {elegida.estado === 'fresca' ? 'El modelo la ve fresca' : 'El modelo la ve podrida'} con {porcentaje(elegida.probabilidad)} de seguridad.</p>
                  </div>
                </div>
                <Medidor valor={elegida.prob_podrida} desde={ajustes.descuentoDesde} retirar={ajustes.retirarDesde} />
                <Ranking filas={elegida.ranking.slice(0, 4)} />
              </div>
            )}

            <Reglas />
          </aside>
        </div>
      )}

      <Camara abierta={camara} onCerrar={() => setCamara(false)} onFoto={analizar} />
    </>
  )
}
