import type { ReactElement } from 'react'
import { usarEstado } from './lib/contexto'
import { usarRuta, type Vista } from './lib/ruta'
import { IconoPrecios, IconoRevisar, Marca } from './components/Iconos'
import { Precios } from './vistas/Precios'
import { Revisar } from './vistas/Revisar'

const NAV: { vista: Vista; texto: string; icono: ReactElement }[] = [
  { vista: 'revisar', texto: 'Revisar fruta', icono: <IconoRevisar /> },
  { vista: 'precios', texto: 'Precios', icono: <IconoPrecios /> },
]

export function App() {
  const ruta = usarRuta()
  const { config, errorConfig, ajustes } = usarEstado()
  const listo = !!config && !!ajustes

  return (
    <div className="app">
      <aside className="rail">
        <a className="rail__marca" href="#/revisar" aria-label="FrutaCheck, ir al inicio">
          <Marca />
          <span className="rail__nombre">FrutaCheck</span>
        </a>
        <p className="rail__lema">Revisa la fruta antes de venderla</p>
        <nav className="nav" aria-label="Secciones">
          {NAV.map((n) => (
            <a key={n.vista} className="nav__item" href={`#/${n.vista}`} aria-current={ruta.vista === n.vista ? 'page' : undefined}>
              {n.icono}
              {n.texto}
            </a>
          ))}
        </nav>
        <div className="rail__pie">
          <span className={`estado${errorConfig ? ' estado--error' : ''}`}>
            <i />
            {errorConfig ? 'Sin conexión con la API' : listo ? 'Modelos listos' : 'Cargando modelos…'}
          </span>
          <span>Las fotos se analizan y no se guardan.</span>
        </div>
      </aside>

      <main className="trabajo">
        {errorConfig && (
          <div className="vacio">
            <h2 className="titulo">No se pudo conectar con el servidor</h2>
            <p>{errorConfig}</p>
            <p>Inicie la API con <code>python -m uvicorn api.main:app --port 8000</code> y recargue la página.</p>
          </div>
        )}
        {!errorConfig && !listo && <p className="suave">Cargando los modelos…</p>}
        {listo && (
          <>
            <section className="vista" hidden={ruta.vista !== 'revisar'}><Revisar ruta={ruta} activa={ruta.vista === 'revisar'} /></section>
            <section className="vista" hidden={ruta.vista !== 'precios'}><Precios /></section>
          </>
        )}
      </main>
    </div>
  )
}
