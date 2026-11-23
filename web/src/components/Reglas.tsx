import { usarPanel } from '../lib/contexto'
import { porcentaje } from '../lib/format'
import { Deslizador } from './Deslizador'

/** Reglas de descuento y retiro; los cambios se aplican al instante a los resultados en pantalla. */
export function Reglas() {
  const { ajustes, cambiarAjustes, restablecer } = usarPanel()
  return (
    <div className="bloque">
      <h2>
        Reglas de descuento
        <button type="button" className="enlace" onClick={restablecer}>Restablecer</button>
      </h2>
      <Deslizador
        etiqueta="Descontar desde"
        valor={ajustes.descuentoDesde}
        minimo={0.05}
        maximo={0.95}
        paso={0.05}
        formato={porcentaje}
        onCambio={(v) => cambiarAjustes({ descuentoDesde: v })}
        ayuda="Probabilidad de estar podrida a partir de la cual la fruta baja de precio."
      />
      <Deslizador
        etiqueta="Retirar desde"
        valor={ajustes.retirarDesde}
        minimo={0.05}
        maximo={1}
        paso={0.05}
        formato={porcentaje}
        onCambio={(v) => cambiarAjustes({ retirarDesde: v })}
        ayuda="Por encima de este valor la fruta ya no se vende."
      />
      <Deslizador
        etiqueta="Descuento aplicado"
        valor={ajustes.descuento}
        minimo={0.05}
        maximo={0.9}
        paso={0.05}
        formato={porcentaje}
        onCambio={(v) => cambiarAjustes({ descuento: v })}
      />
      <Deslizador
        etiqueta="Seguridad mínima del modelo"
        valor={ajustes.confianza}
        minimo={0.3}
        maximo={0.95}
        paso={0.05}
        formato={porcentaje}
        onCambio={(v) => cambiarAjustes({ confianza: v })}
        ayuda="Si el modelo duda más que esto sobre qué fruta es, pasa a revisión manual."
      />
      <a className="enlace" href="#/precios">Cambiar los precios por fruta</a>
    </div>
  )
}
