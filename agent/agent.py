"""Asistente de Física I - UBA con AG-UI y ADK"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import json
import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

# ADK imports
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import ToolContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

from pydantic import BaseModel, Field

# Importar componentes de embeddings y Qdrant
import torch
from transformers import AutoTokenizer, AutoModel
from qdrant_client import AsyncQdrantClient
import asyncio

# ========================================
# ESTADO DE LA CONVERSACIÓN
# ========================================

class ConversacionState(BaseModel):
    """Estado de la conversación con el usuario."""
    historial: List[Dict[str, str]] = Field(
        default_factory=list,
        description='Historial de consultas y respuestas',
    )
    ultimo_tema: Optional[str] = Field(
        default=None,
        description='Último tema clasificado'
    )
    contexto_documentos: Optional[str] = Field(
        default=None,
        description='Últimos fragmentos relevantes encontrados'
    )


# ========================================
# CONFIGURACIÓN GLOBAL
# ========================================

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "documentos_pdf")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Inicializar modelo de embeddings globalmente
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
embedding_model = AutoModel.from_pretrained(MODEL_NAME).to(device)

# Temario del curso (se puede cargar desde archivo)
TEMARIO_FISICA = """
FÍSICA I - UNIVERSIDAD DE BUENOS AIRES

UNIDAD 1: CINEMÁTICA
- Movimiento en una dimensión
- Movimiento en dos y tres dimensiones
- Movimiento circular
- Movimiento relativo

UNIDAD 2: DINÁMICA
- Leyes de Newton
- Fuerzas y diagramas de cuerpo libre
- Fricción y resistencia
- Movimiento circular dinámico

UNIDAD 3: TRABAJO Y ENERGÍA
- Trabajo mecánico
- Energía cinética y potencial
- Conservación de la energía
- Potencia

UNIDAD 4: ONDAS Y SONIDO
- Movimiento armónico simple
- Ondas mecánicas
- Efecto Doppler
- Interferencia y resonancia

UNIDAD 5: MECÁNICA DE FLUIDOS
- Estática de fluidos
- Dinámica de fluidos
- Ecuación de Bernoulli
"""


# ========================================
# HERRAMIENTAS (TOOLS)
# ========================================

def clasificar_consulta(
    tool_context: ToolContext,
    consulta: str
) -> Dict[str, Any]:
    """
    Clasifica una consulta del usuario según el temario de física.
    
    Args:
        consulta: La consulta del usuario a clasificar
    
    Returns:
        Dict con tema, subtemas y keywords
    """
    try:
        # Obtener historial del contexto
        historial = tool_context.state.get("historial", [])
        contexto_previo = ""
        
        if historial:
            ultimas_3 = historial[-3:]
            contexto_previo = "\n".join([
                f"Usuario: {h['consulta']}\nAsistente: {h['respuesta'][:200]}..."
                for h in ultimas_3
            ])
        
        # Construir prompt para clasificación
        prompt = f"""
TEMARIO:
{TEMARIO_FISICA}

CONTEXTO DE CONVERSACIÓN PREVIA:
{contexto_previo if contexto_previo else "No hay conversación previa"}

CONSULTA DEL USUARIO:
{consulta}

Clasifica esta consulta según el temario. Responde SOLO con:
TEMA: [número y título]
SUBTEMAS: [lista]
KEYWORDS: [palabras clave separadas por comas]
"""
        
        # Aquí simularíamos una llamada al LLM para clasificar
        # En la práctica, esto debería hacerse dentro del agente principal
        return {
            "status": "success",
            "clasificacion": prompt,
            "consulta_original": consulta
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error clasificando consulta: {str(e)}"
        }


async def buscar_documentos_async(query: str, top_k: int = 5) -> List[Dict]:
    """Versión async de búsqueda en Qdrant"""
    try:
        # Generar embedding de la consulta
        inputs = tokenizer(
            [query],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(device)
        
        with torch.no_grad():
            outputs = embedding_model(**inputs)
        
        query_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy().flatten()
        
        # Buscar en Qdrant
        client = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
        results = await client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding.tolist(),
            limit=top_k
        )
        
        # Formatear resultados
        documentos = []
        for i, result in enumerate(results, 1):
            payload = result.payload or {}
            documentos.append({
                "fragmento": i,
                "pdf": payload.get("pdf_name", "N/A"),
                "texto": payload.get("text", "No disponible"),
                "similitud": round(result.score, 4)
            })
        
        return documentos
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return []


def buscar_documentos(
    tool_context: ToolContext,
    consulta_busqueda: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Busca documentos relevantes en la base de datos vectorial.
    
    Args:
        consulta_busqueda: Consulta optimizada para búsqueda
        top_k: Número de documentos a retornar (default 5)
    
    Returns:
        Dict con los documentos encontrados
    """
    try:
        # Ejecutar búsqueda async en un loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        documentos = loop.run_until_complete(
            buscar_documentos_async(consulta_busqueda, top_k)
        )
        loop.close()
        
        # Guardar en el estado para uso posterior
        contexto_docs = "\n\n".join([
            f"--- Fragmento {d['fragmento']} (PDF: {d['pdf']}, similitud: {d['similitud']}) ---\n{d['texto']}"
            for d in documentos
        ])
        
        tool_context.state["contexto_documentos"] = contexto_docs
        
        return {
            "status": "success",
            "total_encontrados": len(documentos),
            "documentos": documentos,
            "contexto_formateado": contexto_docs
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error buscando documentos: {str(e)}",
            "documentos": []
        }


def guardar_interaccion(
    tool_context: ToolContext,
    consulta: str,
    respuesta: str,
    tema: Optional[str] = None
) -> Dict[str, str]:
    """
    Guarda una interacción en el historial de conversación.
    
    Args:
        consulta: Consulta del usuario
        respuesta: Respuesta del asistente
        tema: Tema clasificado (opcional)
    
    Returns:
        Dict indicando éxito
    """
    try:
        if "historial" not in tool_context.state:
            tool_context.state["historial"] = []
        
        tool_context.state["historial"].append({
            "consulta": consulta,
            "respuesta": respuesta,
            "tema": tema
        })
        
        if tema:
            tool_context.state["ultimo_tema"] = tema
        
        return {
            "status": "success",
            "message": "Interacción guardada"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error guardando interacción: {str(e)}"
        }


# ========================================
# CALLBACKS
# ========================================

def on_before_agent(callback_context: CallbackContext):
    """Inicializar estado si no existe"""
    if "historial" not in callback_context.state:
        callback_context.state["historial"] = []
    if "ultimo_tema" not in callback_context.state:
        callback_context.state["ultimo_tema"] = None
    if "contexto_documentos" not in callback_context.state:
        callback_context.state["contexto_documentos"] = None
    
    return None


def before_model_modifier(
    callback_context: CallbackContext, 
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Modifica el prompt del modelo para incluir contexto"""
    agent_name = callback_context.agent_name
    
    if agent_name == "AsistenteFisica":
        # Obtener contexto del estado
        historial = callback_context.state.get("historial", [])
        contexto_docs = callback_context.state.get("contexto_documentos", "")
        ultimo_tema = callback_context.state.get("ultimo_tema", "")
        
        # Construir contexto de conversación
        contexto_conversacion = "No hay conversación previa."
        if historial:
            ultimas_3 = historial[-3:]
            contexto_conversacion = "\n".join([
                f"Usuario: {h['consulta']}\nAsistente: {h['respuesta'][:300]}..."
                for h in ultimas_3
            ])
        
        # Modificar system instruction
        original_instruction = llm_request.config.system_instruction or types.Content(
            role="system", 
            parts=[]
        )
        
        if not isinstance(original_instruction, types.Content):
            original_instruction = types.Content(
                role="system", 
                parts=[types.Part(text=str(original_instruction))]
            )
        
        if not original_instruction.parts:
            original_instruction.parts.append(types.Part(text=""))
        
        # Agregar contexto al inicio del prompt
        prefix = f"""Eres un profesor experto en Física I de la UBA.

TEMARIO DEL CURSO:
{TEMARIO_FISICA}

CONTEXTO DE CONVERSACIÓN PREVIA:
{contexto_conversacion}

ÚLTIMO TEMA DISCUTIDO: {ultimo_tema if ultimo_tema else "Ninguno"}

FRAGMENTOS DE DOCUMENTOS RELEVANTES:
{contexto_docs if contexto_docs else "No hay documentos cargados aún."}

---

"""
        
        modified_text = prefix + (original_instruction.parts[0].text or "")
        original_instruction.parts[0].text = modified_text
        llm_request.config.system_instruction = original_instruction
    
    return None


def after_model_modifier(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Procesa la respuesta del modelo"""
    agent_name = callback_context.agent_name
    
    if agent_name == "AsistenteFisica":
        if llm_response.content and llm_response.content.parts:
            if llm_response.content.role == 'model' and llm_response.content.parts[0].text:
                # Finalizar invocación después de responder
                callback_context._invocation_context.end_invocation = True
    
    return None


# ========================================
# AGENTE PRINCIPAL
# ========================================

fisica_agent = LlmAgent(
    name="AsistenteFisica",
    model="gemini-2.5-flash",
    instruction=f"""Eres un profesor experto en Física I de la Universidad de Buenos Aires.

**TU FLUJO DE TRABAJO:**

1. **Cuando recibas una consulta del usuario:**
   - Primero, usa la herramienta `clasificar_consulta` para identificar el tema
   - Luego, usa `buscar_documentos` con palabras clave relevantes para encontrar información
   - Finalmente, responde de forma clara y didáctica basándote en los documentos encontrados
   - Al terminar, usa `guardar_interaccion` para registrar la conversación

2. **Al responder:**
   - Usa principalmente los fragmentos de documentos encontrados
   - Si la información no es suficiente, usa tu conocimiento general de física (pero acláralo)
   - Estructura tu respuesta con:
     * Explicación conceptual clara
     * Fórmulas relevantes (usa formato LaTeX si es apropiado)
     * Ejemplos prácticos cuando sea posible
   - Usa un tono educativo y accesible
   
3. **IMPORTANTE:**
   - NUNCA digas "Como modelo de lenguaje..." o "Basado en los documentos..."
   - Actúa como un profesor experto con conocimiento profundo
   - Si no encuentras información en los documentos, dilo claramente pero ayuda con lo que sepas

4. **Herramientas disponibles:**
   - `clasificar_consulta`: Para identificar el tema de la consulta
   - `buscar_documentos`: Para encontrar información relevante
   - `guardar_interaccion`: Para registrar la conversación

**EJEMPLO DE FLUJO:**
Usuario: "¿Qué es el efecto Doppler?"
1. Usar clasificar_consulta("¿Qué es el efecto Doppler?")
2. Usar buscar_documentos("efecto Doppler ondas sonido frecuencia", top_k=5)
3. Responder basándote en los documentos encontrados
4. Usar guardar_interaccion con la consulta y tu respuesta
""",
    tools=[clasificar_consulta, buscar_documentos, guardar_interaccion],
    before_agent_callback=on_before_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_modifier
)


# ========================================
# CONFIGURACIÓN DE AG-UI
# ========================================

# Crear instancia de ADK con AG-UI
adk_fisica_agent = ADKAgent(
    adk_agent=fisica_agent,
    app_name="fisica_uba_app",
    user_id="estudiante_fisica",
    session_timeout_seconds=7200,  # 2 horas
    use_in_memory_services=True
)

# Crear aplicación FastAPI
app = FastAPI(
    title="Asistente de Física I - UBA",
    description="Sistema RAG con agentes ADK para consultas de física",
    version="1.0.0"
)

# Agregar el endpoint de ADK
add_adk_fastapi_endpoint(app, adk_fisica_agent, path="/")


# ========================================
# ENDPOINTS ADICIONALES
# ========================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "AsistenteFisica",
        "model": "gemini-2.5-flash"
    }


@app.get("/info")
async def agent_info():
    """Información del agente"""
    return {
        "name": "Asistente de Física I - UBA",
        "description": "Sistema RAG con agentes ADK",
        "features": [
            "Clasificación automática de consultas",
            "Búsqueda en base de datos vectorial (Qdrant)",
            "Respuestas basadas en documentos del curso",
            "Memoria de conversación",
            "Explicaciones didácticas"
        ],
        "tools": [
            "clasificar_consulta - Identifica temas",
            "buscar_documentos - Busca información relevante",
            "guardar_interaccion - Registra conversación"
        ]
    }


# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    import uvicorn
    
    # Verificar variables de entorno
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY no configurada!")
        print("   Configúrala con: export GOOGLE_API_KEY='tu-clave'")
        print("   Obtén una clave en: https://makersuite.google.com/app/apikey")
        print()
    
    if not os.getenv("QDRANT_URL") or not os.getenv("QDRANT_KEY"):
        print("⚠️  Warning: QDRANT_URL o QDRANT_KEY no configuradas!")
        print("   Configúralas en tu archivo .env")
        print()
    
    port = int(os.getenv("PORT", 8000))
    
    print(f"""
    ╔═══════════════════════════════════════════════════════╗
    ║   🎓 Asistente de Física I - UBA                      ║
    ║   Powered by Google ADK + AG-UI                       ║
    ╠═══════════════════════════════════════════════════════╣
    ║   🌐 Servidor: http://0.0.0.0:{port}                 ║
    ║   📚 Agente: AsistenteFisica                          ║
    ║   🤖 Modelo: gemini-2.5-flash                         ║
    ║   💾 Base de datos: Qdrant                            ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=port)