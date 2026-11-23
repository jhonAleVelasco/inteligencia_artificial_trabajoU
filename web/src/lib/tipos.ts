export type Accion = 'normal' | 'descuento' | 'retirar' | 'revisar'
export type Estado = 'fresca' | 'podrida'

export interface FilaRanking {
  clase: string
  nombre: string
  probabilidad: number
}

/** Resultado de clasificar una fruta (lo que devuelve la API). */
export interface Resultado {
  clase: string
  nombre_clase: string
  fruta: string
  nombre: string
  estado: Estado
  probabilidad: number
  prob_podrida: number
  confiable: boolean
  recomendacion: string
  ranking: FilaRanking[]
}

export interface Caja {
  x0: number
  y0: number
  x1: number
  y1: number
}

export interface FrutaDetectada extends Resultado {
  id: number
  accion: Accion
  area: number
  caja: Caja
  recorte: string
}

export interface RespuestaVarias {
  ancho: number
  alto: number
  frutas: FrutaDetectada[]
}

export interface FrutaConfig {
  id: string
  nombre: string
  precio_unidad: number
}

export interface Config {
  frutas: FrutaConfig[]
  por_defecto: {
    confianza: number
    descuento: number
    descuento_desde: number
    retirar_desde: number
  }
  modelo_deteccion: { propio: boolean }
}

/** Reglas que el usuario ajusta en el panel; se recuerdan en este navegador. */
export interface Ajustes {
  confianza: number
  descuento: number
  descuentoDesde: number
  retirarDesde: number
  precios: Record<string, number>
}
