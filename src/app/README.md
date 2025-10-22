# 🎓 Asistente de Física I - UBA (Frontend)

Interfaz de chatbot con Next.js, CopilotKit y AG-UI para el sistema RAG de Física.

## 🚀 Instalación Rápida

### 1. Instalar dependencias

```bash
npm install
# o
pnpm install
# o
yarn install
```

### 2. Configurar variables de entorno

Crea un archivo `.env.local`:

```env
BACKEND_URL=http://localhost:8000
```

### 3. Ejecutar el proyecto

```bash
# Opción 1: Solo frontend (el backend debe estar corriendo por separado)
npm run dev

# Opción 2: Frontend + Backend juntos
npm run dev:all
```

Abre [http://localhost:3000](http://localhost:3000) en tu navegador.

## 📁 Estructura Simple

```
frontend/
├── src/
│   └── app/
│       ├── api/
│       │   └── copilotkit/
│       │       └── route.ts      # Conexión con backend ADK
│       ├── page.tsx              # Interfaz del chatbot
│       ├── layout.tsx            # Layout con CopilotKit Provider
│       └── globals.css           # Estilos
├── .env.local                    # Variables de entorno
└── package.json                  # Dependencias
```

## 🔧 Archivo route.ts

El archivo `src/app/api/copilotkit/route.ts` conecta el frontend con el backend ADK:

```typescript
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const serviceAdapter = new ExperimentalEmptyAdapter();

const runtime = new CopilotRuntime({
  agents: {
    "asistente_fisica": new HttpAgent({
      url: process.env.BACKEND_URL || "http://localhost:8000/"
    }),
  }
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
```

## 📝 Scripts Disponibles

```bash
npm run dev          # Iniciar frontend (puerto 3000)
npm run dev:all      # Iniciar frontend + backend
npm run build        # Build de producción
npm run start        # Servidor de producción
npm run lint         # Linter
```

## 🎨 Personalizar el Chat

### Cambiar mensajes de bienvenida

En `src/app/page.tsx`:

```typescript
labels={{
  title: "Tu título",
  initial: "Tu mensaje de bienvenida...",
  placeholder: "Tu placeholder...",
}}
```

### Cambiar colores

En `src/app/globals.css`:

```css
:root {
  --copilot-kit-primary-color: #2563eb;  /* Tu color */
}
```

## 🐛 Troubleshooting

### Error: "Cannot connect to agent"

1. Verifica que el backend esté corriendo en `http://localhost:8000`
2. Comprueba que `BACKEND_URL` en `.env.local` sea correcto
3. Revisa los logs del backend

### Error: "Module not found"

```bash
# Reinstalar dependencias
rm -rf node_modules package-lock.json
npm install
```

### El chat no responde

1. Abre las DevTools del navegador (F12)
2. Ve a la pestaña Network
3. Busca errores en las peticiones a `/api/copilotkit`
4. Verifica los logs del servidor backend

## 📚 Dependencias Principales

```json
{
  "@ag-ui/client": "^0.0.38",
  "@copilotkit/react-core": "1.10.4",
  "@copilotkit/react-ui": "1.10.4",
  "@copilotkit/runtime": "1.10.4",
  "next": "15.3.2",
  "react": "^19.0.0"
}
```

## 🔗 Enlaces Útiles

- [CopilotKit Docs](https://docs.copilotkit.ai)
- [AG-UI GitHub](https://github.com/google/ag-ui)
- [Next.js Docs](https://nextjs.org/docs)
- [Google ADK Docs](https://google.github.io/adk-docs/)

## ✨ Características

✅ Interfaz de chat simple y limpia  
✅ Conexión con backend ADK vía AG-UI  
✅ Sistema RAG con búsqueda en documentos  
✅ Respuestas basadas en material del curso  
✅ Memoria de conversación  
✅ Estilos personalizables  

## 📄 Licencia

MIT