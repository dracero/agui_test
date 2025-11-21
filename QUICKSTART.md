# 🚀 Guía de Inicio Rápido

Esta guía te ayudará a poner en marcha el proyecto en menos de 5 minutos.

## ⚡ Pasos Rápidos

### 1. Instalar Dependencias

```bash
# Instalar Node.js dependencies
npm install

# Instalar Python dependencies
cd agent
uv sync
cd ..
```

### 2. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env y agregar tus credenciales
nano .env  # o usa tu editor favorito
```

**Mínimo requerido en `.env`:**
```env
GOOGLE_API_KEY=tu_api_key_de_google
QDRANT_URL=tu_url_de_qdrant
QDRANT_KEY=tu_key_de_qdrant
DIR_PDF=/ruta/a/tus/pdfs
```

### 3. Agregar PDFs

```bash
# Crear directorio de PDFs
mkdir -p pdfs

# Copiar tus PDFs de física
cp /ruta/a/tus/pdfs/*.pdf pdfs/
```

### 4. Ejecutar

```bash
npm run dev
```

✅ Abre `http://localhost:3000` en tu navegador

## 🔑 Obtener Credenciales Rápidamente

### Google Gemini API (2 minutos)
1. Ve a https://makersuite.google.com/app/apikey
2. Haz clic en "Create API Key"
3. Copia la key → pega en `.env`

### Qdrant Cloud (5 minutos)
1. Ve a https://cloud.qdrant.io/
2. Crea una cuenta gratis
3. Crea un cluster (Free tier disponible)
4. Copia URL y API Key → pega en `.env`

**O usa Qdrant Local:**
```bash
docker run -p 6333:6333 qdrant/qdrant
```
Luego en `.env`:
```env
QDRANT_URL=http://localhost:6333
QDRANT_KEY=
```

## 🐛 Problemas Comunes

### "Cannot find module 'next'"
```bash
npm install
```

### "GOOGLE_API_KEY not found"
- Verifica que `.env` existe en la raíz del proyecto
- Reinicia el servidor después de crear `.env`

### "Connection to Qdrant failed"
- Verifica que Qdrant esté corriendo
- Comprueba que la URL y key sean correctas

### Advertencias de Langfuse
- Son normales, puedes ignorarlas
- No afectan la funcionalidad

## 📝 Comandos Útiles

```bash
# Desarrollo (todo junto)
npm run dev

# Solo frontend
npm run dev:ui

# Solo backend
npm run dev:agent

# Build de producción
npm run build

# Limpiar y reinstalar
rm -rf node_modules .next agent/.venv
npm install
cd agent && uv sync
```

## 🎯 Verificación Rápida

Si todo está bien, deberías ver:
```
✅ APIs configuradas
✅ AsistenteFisica inicializado correctamente
✅ Modelos inicializados
✅ Memoria semántica inicializada
✅ Agentes ADK creados correctamente
✅ Componentes ADK inicializados
✅ Modelo de embeddings inicializado
✅ Todos los componentes inicializados
📁 Directorio de PDFs: /ruta/a/pdfs
📚 Encontrados X archivos PDF
✅ Temario extraído correctamente
X chunks almacenados en Qdrant
```

## 📚 Más Información

Para documentación completa, consulta [README.md](./README.md)

---

¿Problemas? Abre un issue en GitHub o revisa la sección de troubleshooting en el README.
