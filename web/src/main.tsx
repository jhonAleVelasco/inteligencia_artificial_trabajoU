import '@fontsource-variable/archivo/wdth.css'
import './estilos.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { Proveedor } from './lib/contexto'

createRoot(document.getElementById('raiz')!).render(
  <StrictMode>
    <Proveedor>
      <App />
    </Proveedor>
  </StrictMode>,
)
