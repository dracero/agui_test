#!/usr/bin/env bash
# scripts/start-agent.sh - Script mejorado para iniciar el backend del Asistente de Física

set -euo pipefail

# Manejo de señales para limpiar si es necesario
trap 'echo "\nInterrumpido. Saliendo..."; exit 130' SIGINT SIGTERM

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════╗
║   🎓 Asistente de Física I - UBA                      ║
║   Iniciando Backend (Python + ADK + AG-UI)            ║
╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Cambiar al directorio agent
cd "$(dirname "$0")/../agent" || exit 1

# Verificar archivo agent.py
if [ ! -f "agent.py" ]; then
    echo -e "${RED}❌ Error: agent.py no encontrado${NC}"
    exit 1
fi

# Detectar python (prefiere python3)
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo -e "${RED}❌ No se encontró Python en el PATH${NC}"
  exit 1
fi

# Crear y activar entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Creando entorno virtual...${NC}"
    $PYTHON -m venv .venv
    echo -e "${GREEN}✅ Entorno virtual creado${NC}"
fi

# Activar entorno virtual
echo -e "${BLUE}🔧 Activando entorno virtual...${NC}"
# shellcheck disable=SC1091
source .venv/bin/activate

# Asegurarse de usar el python y pip del venv
VENV_PY=".venv/bin/python"
PIP_COMMAND="${VENV_PY} -m pip"

# Instalar/actualizar dependencias
echo -e "${BLUE}📦 Instalando dependencias (si es necesario)...${NC}"
${PIP_COMMAND} install --upgrade pip >/dev/null 2>&1 || true
${PIP_COMMAND} install -r requirements.txt >/dev/null 2>&1 || true
echo -e "${GREEN}✅ Dependencias (procesadas)${NC}"

# Verificar variables de entorno
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: Archivo .env no encontrado en $(pwd)${NC}"
    echo -e "${YELLOW}💡 Crea un archivo .env basado en .env.example${NC}"
    exit 1
fi

# Cargar variables de entorno de forma segura (ignora comentarios y líneas vacías)
# Intentamos usar python-dotenv si está disponible
if ${PIP_COMMAND} show python-dotenv >/dev/null 2>&1; then
  # Usar python para exportar variables (maneja espacios y comillas)
  eval "$(python - <<PYTHON
from dotenv import dotenv_values
import shlex, sys
vals = dotenv_values('.env')
for k,v in vals.items():
    if v is None:
        continue
    print(f"export {k}={shlex.quote(str(v))}")
PYTHON
)"
else
  # Fallback simple (puede fallar con valores con espacios)
  set -o allexport
  # shellcheck disable=SC1090
  source <(grep -v '^\s*#' .env | sed '/^\s*$/d') || true
  set +o allexport
fi

# Verificar variables críticas
MISSING_VARS=()
[ -z "${GOOGLE_API_KEY:-}" ] && MISSING_VARS+=("GOOGLE_API_KEY")
[ -z "${QDRANT_URL:-}" ] && MISSING_VARS+=("QDRANT_URL")
[ -z "${QDRANT_KEY:-}" ] && MISSING_VARS+=("QDRANT_KEY")

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}❌ Faltan variables de entorno:${NC}"
    printf '%s\n' "${MISSING_VARS[@]}" | sed 's/^/   - /'
    exit 1
fi

echo -e "${GREEN}✅ Variables configuradas${NC}"

# Verificar si la BD está inicializada
if [ ! -f "pdf_metadata.json" ]; then
    echo -e "${YELLOW}⚠️  Base de datos no inicializada${NC}"
    # Si se exportó SKIP_DB_INIT_PROMPT=1 o se pasó --yes, saltar
    if [ "${SKIP_DB_INIT_PROMPT:-0}" = "1" ] || [ "${NONINTERACTIVE:-0}" = "1" ]; then
        echo -e "${YELLOW}⚠️  No se inicializará la BD en modo no interactivo${NC}"
    else
        read -p "¿Deseas inicializarla ahora? (s/N): " -n 1 -r || true
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            ${PYTHON} init_database.py
        else
            echo -e "${YELLOW}⚠️  Continuando sin inicializar BD...${NC}"
        fi
    fi
fi

# Iniciar servidor
echo -e "${GREEN}"
echo "🚀 Iniciando servidor en http://localhost:8000"
echo -e "${NC}"

# Ejecutar con el python del venv
exec .venv/bin/python agent.py