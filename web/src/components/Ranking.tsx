import { porcentaje } from '../lib/format'
import type { FilaRanking } from '../lib/tipos'

/** Probabilidad que el modelo da a cada clase, de mayor a menor. */
export function Ranking({ filas }: { filas: FilaRanking[] }) {
  return (
    <ol className="ranking">
      {filas.map((f, i) => (
        <li key={f.clase} className={i === 0 ? 'primero' : undefined}>
          <span>
            {f.nombre}
            <i>
              <b style={{ width: `${Math.max(f.probabilidad * 100, 0.5)}%` }} />
            </i>
          </span>
          <span className="num">{porcentaje(f.probabilidad)}</span>
        </li>
      ))}
    </ol>
  )
}
