"""Asistente de Física I - UBA con AG-UI y ADK"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import json
import os
import time
import asyncio
import nest_asyncio
import torch
from typing import Dict, List, Optional, Any
from fastapi import FastAPI
from contextlib import asynccontextmanager
from PyPDF2 import PdfReader
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from transformers import AutoTokenizer, AutoModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

# Imports de Google ADK
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from pydantic import BaseModel, ConfigDict
from google.genai import types, Client

# Aplicar nest_asyncio para permitir loops anidados
nest_asyncio.apply()

# Mock observe decorator if langfuse is not configured or fails
try:
    from langfuse import observe
except ImportError:
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

class AsistenteFisica:
    """Clase unificada para el asistente de física con procesamiento de PDFs, RAG y memoria semántica usando Google ADK"""

    def __init__(self):
        # Configurar APIs
        self._setup_apis()

        # Inicializar componentes
        self.llm = None
        self.adk_model = None
        self.memoria_semantica = None
        self.agents = {}
        self.session_service = None
        self.runner = None
        self.temario = ""
        self.contenido_completo = ""

        # Configuración de embedding
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.tokenizer = None
        self.model = None

        # Configuración de Qdrant
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_KEY")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "documentos_pdf")

        print("✅ AsistenteFisica inicializado correctamente")

    def _setup_apis(self):
        """Configurar las APIs necesarias"""
        # Ya cargadas por load_dotenv
        if not os.getenv("GOOGLE_API_KEY"):
            print("⚠️ GOOGLE_API_KEY no encontrada en variables de entorno")
        print("✅ APIs configuradas")

    def inicializar_componentes(self):
        """Inicializar todos los componentes del asistente"""
        self._inicializar_modelos()
        self._inicializar_memoria()
        self._inicializar_adk()
        self._inicializar_modelo_embedding()
        print("✅ Todos los componentes inicializados")

    ###
    # Función auxiliar para obtener respuestas
    async def _get_agent_response(self, agent, input_data):
        """Función auxiliar para obtener respuesta de un agente ADK"""
        try:
            # Formatear el prompt para el agente
            if isinstance(input_data, dict):
                prompt = self._format_prompt_for_agent(agent.name, input_data)
            else:
                prompt = str(input_data)

            # Método 1: Usar Runner.run() - La forma estándar en ADK
            try:
                # Crear runner con el agente
                runner = Runner(agent)

                # Ejecutar el agente con el prompt
                response = await runner.run(prompt)

                # Extraer la respuesta del objeto response
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'content'):
                    return response.content
                elif hasattr(response, 'message'):
                    return response.message
                else:
                    return str(response)

            except Exception as runner_error:
                print(f"Error con Runner.run(): {runner_error}")
                
                # Fallback manual
                raise runner_error

        except Exception as e:
            print(f"Error ejecutando agente {agent.name}: {e}")

            # Fallback: usar el modelo LLM directamente
            try:
                messages = [
                    SystemMessage(content=getattr(agent, 'instruction', 'You are a helpful AI assistant.')),
                    HumanMessage(content=prompt)
                ]
                response = self.llm.invoke(messages)
                return response.content
            except Exception as fallback_error:
                print(f"Error en fallback para agente {agent.name}: {fallback_error}")
                return None
    ###

    def _format_prompt_for_agent(self, agent_name, data):
        """Formatear el prompt según el agente específico"""
        if agent_name == "clasificador":
            return f"""
                    TEMARIO DE FÍSICA:
                    {data.get('temario', '')}

                    CONTEXTO DE CONVERSACIÓN PREVIA:
                    {data.get('contexto_memoria', '')}

                    CONSULTA DEL USUARIO:
                    {data.get('consulta_usuario', '')}

                    Clasifica esta consulta según el temario proporcionado.
                    """
        elif agent_name == "buscador":
                                return f"""
                    CLASIFICACIÓN:
                    {data.get('clasificacion', '')}

                    CONSULTA ORIGINAL:
                    {data.get('consulta_original', '')}

                    Genera la mejor consulta de búsqueda para esta información.
                    """
        elif agent_name == "respondedor":
                                return f"""
                    **CONSULTA ORIGINAL DEL USUARIO:**
                    {data.get('consulta_usuario', '')}

                    **CONTEXTO DE CONVERSACIÓN ANTERIOR:**
                    {data.get('contexto_memoria', '')}

                    **CLASIFICACIÓN TEMÁTICA:**
                    {data.get('clasificacion', '')}

                    **FRAGMENTOS DE DOCUMENTOS RELEVANTES:**
                    {data.get('contexto_documentos', '')}

                    Proporciona una respuesta completa y didáctica.
                    """
        return str(data)

    def _inicializar_modelos(self):
        """Inicializar los modelos de lenguaje"""
        # Configuración común para Gemini
        gemini_config = {
            "model": "gemini-2.5-flash",
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "temperature": 0,
            "max_output_tokens": None,
        }

        # LLM para LangChain (para compatibilidad con memoria)
        self.llm = ChatGoogleGenerativeAI(**gemini_config)

        print("✅ Modelos inicializados")

    def _inicializar_memoria(self):
        """Inicializar la memoria semántica"""
        self.memoria_semantica = self.SemanticMemory(llm=self.llm)
        print("✅ Memoria semántica inicializada")

    def _inicializar_adk(self):
        """Inicializar componentes ADK"""
        # Crear servicio de sesiones
        self.session_service = InMemorySessionService()

        # Crear agentes ANTES del Runner
        self._crear_agentes()

        # Crear runner principal (opcional, ya que usamos invoke directamente)
        self.runner = Runner(
            app_name="Asistente de Física",
            agent=self.classifier_agent,
            session_service=self.session_service
        )

        print("✅ Componentes ADK inicializados")

    def _crear_agentes(self):
        """Crear los agentes ADK con la sintaxis correcta."""
        
        # Agente Clasificador
        self.classifier_agent = LlmAgent(
            name="clasificador",
            model="gemini-2.5-flash",
            description="Agente especializado en clasificar consultas de física según el temario proporcionado",
            instruction="""Eres un agente especializado en clasificar consultas de física según el temario proporcionado.
                            A partir de la consulta de usuario y el contexto, realiza la clasificación.

                            Debes proporcionar tu respuesta en el siguiente formato, y nada más:
                            TEMA: [número y título]
                            SUBTEMAS: [lista]
                            KEYWORDS: [palabras clave]
                            """
        )

        # Agente Buscador
        self.search_agent = LlmAgent(
            name="buscador",
            model="gemini-2.5-flash",
            description="Agente de búsqueda especializado en física",
            instruction="""Eres un agente de búsqueda especializado en física.
Recibes una clasificación temática y una consulta original.
Tu tarea es generar la mejor consulta de búsqueda posible para encontrar esta información en una base de datos vectorial.

Responde SOLAMENTE con la consulta de búsqueda optimizada, sin explicaciones adicionales.
"""
        )

        # Agente de Respuesta
        self.response_agent = LlmAgent(
            name="respondedor",
            model="gemini-2.5-flash",
            description="Profesor experto en física que proporciona explicaciones claras y precisas",
            instruction="""Eres un profesor experto en física que proporciona explicaciones claras, precisas y didácticas.
Tu objetivo es responder a la consulta del usuario basándote en la información proporcionada.

**Tus Reglas:**
- Usa principalmente los "FRAGMENTOS DE DOCUMENTOS RELEVANTES" para construir tu respuesta.
- Si la información no es suficiente en los documentos, puedes usar tu conocimiento general, pero siempre aclara que la información no proviene de los documentos proporcionados.
- Usa el "CONTEXTO DE CONVERSACIÓN ANTERIOR" para que tu respuesta fluya naturalmente si esto es parte de un diálogo.
- Estructura tu respuesta de manera clara, usando ecuaciones (en formato de texto) cuando sea apropiado y explicando los conceptos paso a paso.
- IMPORTANTE: Nunca digas frases como "Como modelo de lenguaje..." o "Basado en la información...". Actúa como un profesor experto con pleno conocimiento.
"""
        )

        self.agents = {
            'classifier': self.classifier_agent,
            'search': self.search_agent,
            'response': self.response_agent
        }
        print("✅ Agentes ADK creados correctamente")

    def _inicializar_modelo_embedding(self):
        """Inicializar el modelo de embeddings"""
        # Forzar CPU para evitar warnings de CUDA con hardware antiguo
        device = "cpu" 
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(device)
        print("✅ Modelo de embeddings inicializado")

    def leer_pdf(self, nombre_archivo):
        """Leer contenido de un archivo PDF"""
        try:
            reader = PdfReader(nombre_archivo)
            return "".join(page.extract_text() for page in reader.pages)
        except Exception as e:
            print(f"Error al leer {nombre_archivo}: {e}")
            return ""

    @observe(name="temario", as_type="generation")
    def procesar_pdfs_temario(self, archivos_pdf):
        """Procesar PDFs para extraer el temario"""
        contenido_completo = ""

        for archivo in archivos_pdf:
            if os.path.exists(archivo):
                contenido_completo += f"\n--- Contenido de {archivo} ---\n"
                contenido_completo += self.leer_pdf(archivo)
        
        if not contenido_completo:
            print("⚠️ No se encontró contenido en los PDFs para extraer temario.")
            # Intentar recuperar de Qdrant si no hay PDFs locales
            return "Temario no disponible localmente. Se usará información de la base de datos."

        self.contenido_completo = contenido_completo

        # Extraer temario usando LangChain (para compatibilidad)
        system_message = f"""
Eres un experto profesor Física I de la Universidad de Buenos Aires.
Tu tarea es responder preguntas sobre el temario que tiene en los archivos que lees, proporcionando explicaciones claras, detalladas y ejemplos relevantes.
Responde solo con el contenido, si no está en el contenido di que no tienes eso en tu base de datos.
Utiliza el siguiente contenido como referencia para tus respuestas:
---
{self.contenido_completo}
---
"""

        user_question = "Sobre que contenidos podes contestarme"

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_question),
        ]

        ai_msg = self.llm.invoke(messages)
        self.temario = ai_msg.content

        # Actualizar el temario en el agente clasificador
        if hasattr(self, 'classifier_agent'):
            self.classifier_agent.instruction = f"""Eres un agente especializado en clasificar consultas de física según el temario proporcionado.
Debes proporcionar:
1. El número y título del tema principal
2. Los subtemas relevantes
3. Palabras clave para búsqueda

Formato de respuesta:
TEMA: [número y título]
SUBTEMAS: [lista]
KEYWORDS: [palabras clave]

TEMARIO DE FÍSICA:
{self.temario}
"""

        print("✅ Temario extraído correctamente")
        return self.temario

    def split_into_chunks(self, text, chunk_size=2000):
        """Dividir texto en chunks"""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def generate_embeddings(self, chunks, batch_size=32):
        """Generar embeddings para los chunks"""
        embeddings = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.model.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
            embeddings.extend(outputs.last_hidden_state[:, 0, :].cpu().numpy())
        return embeddings

    async def store_in_qdrant(self, points):
        """Almacenar puntos en Qdrant"""
        client = AsyncQdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)

        # Crear colección si no existe
        try:
            await client.get_collection(self.collection_name)
        except Exception:
            await client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=len(points[0].vector), distance=Distance.COSINE)
            )
            print(f"Colección '{self.collection_name}' creada")

        # Insertar datos
        await client.upsert(collection_name=self.collection_name, points=points, wait=True)
        print(f"{len(points)} chunks almacenados en Qdrant")

    @observe(name="procesar_y_almacenar_pdfs", as_type="span")
    async def procesar_y_almacenar_pdfs(self, pdf_files):
        """Procesar PDFs y almacenar en Qdrant"""
        all_chunks = []
        pdf_metadata = []
        global_id_counter = 0

        for pdf_file in pdf_files:
            if not os.path.exists(pdf_file):
                # print(f"⚠️ {pdf_file} no encontrado")
                continue

            # Procesar PDF
            text = self.leer_pdf(pdf_file)
            if text:
                chunks = self.split_into_chunks(text)

                # Registrar metadatos
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    pdf_metadata.append({
                        "pdf_name": pdf_file,
                        "chunk_id": i,
                        "global_id": global_id_counter
                    })
                    global_id_counter += 1

        if not all_chunks:
            # print("⚠️ No se encontraron chunks para procesar")
            return

        # Generar embeddings
        embeddings = self.generate_embeddings(all_chunks)

        # Generar puntos para Qdrant
        points = [
            PointStruct(
                id=meta["global_id"],
                vector=embedding.tolist(),
                payload={
                    "pdf_name": meta["pdf_name"],
                    "chunk_id": meta["chunk_id"],
                    "text": all_chunks[idx]
                }
            )
            for idx, (meta, embedding) in enumerate(zip(pdf_metadata, embeddings))
        ]

        # Almacenar en Qdrant
        await self.store_in_qdrant(points)

        # Guardar metadatos en JSON
        metadata_dict = {
            p.id: {
                "pdf": p.payload["pdf_name"],
                "chunk": p.payload["text"]
            } for p in points
        }

        with open("pdf_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, ensure_ascii=False, indent=4)
        print("✅ Metadatos guardados en 'pdf_metadata.json'")

    @observe(name="search_documents", as_type="span")
    async def search_documents(self, query, top_k=5):
        """Realizar búsqueda en Qdrant"""
        try:
            client = AsyncQdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)

            # Verificar conexión
            try:
                await client.get_collection(self.collection_name)
                # print("✅ Conexión a Qdrant exitosa")
            except Exception as e:
                print(f"❌ Error al conectar con Qdrant: {str(e)}")
                return []

            # Generar embedding de la consulta
            inputs = self.tokenizer(
                [query],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.model.device)

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Extraer correctamente el embedding y convertir a lista
            query_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            query_embedding = query_embedding.flatten()

            # print(f"🔍 Embedding shape: {query_embedding.shape}")

            # Buscar en Qdrant
            results = await client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k
            )

            # Formatear resultados
            formatted_results = []
            metadata = {}

            if os.path.exists("pdf_metadata.json"):
                with open("pdf_metadata.json", "r", encoding="utf-8") as f:
                    metadata = json.load(f)

            for result in results:
                meta = metadata.get(str(result.id), {})
                payload = result.payload or {}

                formatted_results.append({
                    "pdf": meta.get("pdf", payload.get("pdf_name", "N/A")),
                    "texto": meta.get("chunk", payload.get("text", "Texto no disponible")),
                    "similitud": round(result.score, 4)
                })

            return formatted_results

        except Exception as e:
            error_msg = f"Error en la búsqueda: {str(e)}"
            print(f"❌ {error_msg}")
            return [{"pdf": "Error", "texto": error_msg, "similitud": 0}]

    # Función de flujo corregida
    @observe(name="iniciar_flujo_adk_corregido", as_type="span")
    async def iniciar_flujo(self, consulta_usuario: str, user_id: str = "default_user"):
        """
        Iniciar el flujo completo de procesamiento usando Google ADK
        """
        print(f"📝 Consulta recibida de '{user_id}': {consulta_usuario}")
        trayectoria = []
        inicio_total = time.time()

        # Obtener contexto de memoria semántica
        contexto_memoria = self.memoria_semantica.get_context()

        try:
            # --- Paso 1: Clasificación ---
            inicio_paso = time.time()

            clasificacion_data = {
                "consulta_usuario": consulta_usuario,
                "contexto_memoria": contexto_memoria,
                "temario": self.temario
            }

            clasificacion = await self._get_agent_response(
                self.classifier_agent,
                clasificacion_data
            )

            tiempo_clasificacion = time.time() - inicio_paso

            # Verificar que la respuesta no sea None
            if clasificacion is None:
                # Fallback si falla la clasificación
                clasificacion = "TEMA: Consulta General\nSUBTEMAS: []\nKEYWORDS: []"

            trayectoria.append({
                "agente": "Clasificador",
                "respuesta": clasificacion,
                "tiempo": tiempo_clasificacion
            })
            print(f"✅ Clasificación completada en {tiempo_clasificacion:.2f}s")

            # --- Paso 2: Generar consulta de búsqueda ---
            inicio_paso = time.time()

            search_data = {
                "clasificacion": clasificacion,
                "consulta_original": consulta_usuario,
                "contexto_conversacion": contexto_memoria
            }

            consulta_busqueda = await self._get_agent_response(
                self.search_agent,
                search_data
            )

            tiempo_query = time.time() - inicio_paso

            if consulta_busqueda is None:
                consulta_busqueda = consulta_usuario

            trayectoria.append({
                "agente": "GeneraciónConsulta",
                "respuesta": consulta_busqueda,
                "tiempo": tiempo_query
            })
            print(f"✅ Consulta de búsqueda generada en {tiempo_query:.2f}s")

            # --- Paso 3: Realizar búsqueda en Qdrant ---
            inicio_paso = time.time()
            resultados_busqueda = await self.search_documents(consulta_busqueda)
            tiempo_busqueda = time.time() - inicio_paso

            trayectoria.append({
                "agente": "BúsquedaQdrant",
                "respuesta": f"Encontrados {len(resultados_busqueda)} documentos",
                "tiempo": tiempo_busqueda
            })
            print(f"✅ Búsqueda en Qdrant completada en {tiempo_busqueda:.2f}s")

            # --- Paso 4: Generar respuesta final ---
            inicio_paso = time.time()
            contexto_busqueda = "\n".join([
                f"--- Fragmento {i} (PDF: {res['pdf']}) ---\n{res['texto']}"
                for i, res in enumerate(resultados_busqueda, 1)
            ])

            response_data = {
                "consulta_usuario": consulta_usuario,
                "contexto_memoria": contexto_memoria,
                "clasificacion": clasificacion,
                "contexto_documentos": contexto_busqueda
            }

            respuesta_final = await self._get_agent_response(
                self.response_agent,
                response_data
            )

            tiempo_respuesta = time.time() - inicio_paso

            if respuesta_final is None:
                raise Exception("La respuesta del agente respondedor es None")

            trayectoria.append({
                "agente": "RespondeConsulta",
                "respuesta": respuesta_final,
                "tiempo": tiempo_respuesta
            })
            print(f"✅ Respuesta final generada en {tiempo_respuesta:.2f}s")

            # Actualizar la memoria con la nueva interacción
            self.memoria_semantica.add_interaction(consulta_usuario, respuesta_final)

            tiempo_total = time.time() - inicio_total
            
            # Guardar la trayectoria (opcional, puede fallar si no hay permisos)
            try:
                with open("trayectoria_adk.json", "w", encoding="utf-8") as f:
                    json.dump(trayectoria, f, indent=4, ensure_ascii=False)
            except Exception:
                pass

            return respuesta_final

        except Exception as e:
            print(f"❌ Error en el flujo ADK: {e}")
            import traceback
            traceback.print_exc()

            # Devolver una respuesta de fallback usando el conocimiento del modelo
            fallback_response = f"Lo siento, hubo un error técnico al procesar tu consulta. Por favor, intenta de nuevo."
            return fallback_response

    # Clase interna para memoria semántica
    class SemanticMemory:
        def __init__(self, llm, max_entries=10):
            self.conversations = []
            self.max_entries = max_entries
            self.summary = ""
            self.direct_history = ""
            self.llm = llm

            # Usar ChatMessageHistory en lugar de ConversationSummaryBufferMemory
            self.message_history = ChatMessageHistory()

        def add_interaction(self, query, response):
            """Añadir interacción a la memoria"""
            # Añadir a la historia de mensajes
            self.message_history.add_user_message(query)
            self.message_history.add_ai_message(response)
            
            # Guardar en registro de conversaciones
            self.conversations.append({"query": query, "response": response})
            if len(self.conversations) > self.max_entries:
                self.conversations.pop(0)

            # Mantener historial directo de las últimas 3 interacciones
            self.direct_history += f"\nUsuario: {query}\nAsistente: {response}\n"
            if len(self.conversations) > 3:
                recent = self.conversations[-3:]
                self.direct_history = ""
                for conv in recent:
                    self.direct_history += f"\nUsuario: {conv['query']}\nAsistente: {conv['response']}\n"

            # Actualizar resumen
            self.update_summary()

        def update_summary(self):
            """Actualizar resumen de la conversación"""
            try:
                # Obtener los mensajes de la historia
                messages = self.message_history.messages
                
                # Si hay muchos mensajes, generar un resumen usando el LLM
                if len(messages) > 6:
                    # Tomar los primeros mensajes para resumir
                    old_messages = messages[:-6]
                    recent_messages = messages[-6:]
                    
                    # Crear prompt para resumir
                    conversation_text = "\n".join([
                        f"{'Usuario' if msg.type == 'human' else 'Asistente'}: {msg.content}"
                        for msg in old_messages
                    ])
                    
                    summary_prompt = [
                        SystemMessage(content="Resume brevemente la siguiente conversación en 2-3 oraciones."),
                        HumanMessage(content=conversation_text)
                    ]
                    
                    try:
                        summary_response = self.llm.invoke(summary_prompt)
                        summary_text = summary_response.content
                    except Exception:
                        summary_text = "Conversación previa sobre física."
                    
                    # Construir el contexto con resumen + mensajes recientes
                    recent_text = "\n".join([
                        f"{'Usuario' if msg.type == 'human' else 'Asistente'}: {msg.content}"
                        for msg in recent_messages
                    ])
                    
                    self.summary = f"Resumen de conversación previa: {summary_text}\n\nInteracciones recientes:\n{recent_text}"
                else:
                    # Si hay pocos mensajes, simplemente mostrarlos todos
                    self.summary = f"Interacciones recientes:{self.direct_history}"
                    
            except Exception as e:
                print(f"Error al actualizar resumen: {e}")
                self.summary = f"Interacciones recientes:{self.direct_history}"

        def get_context(self):
            """Obtener contexto actual de la conversación"""
            return self.summary if self.summary.strip() else "No hay conversación previa."


# ========================================
# CONFIGURACIÓN DE AG-UI y FASTAPI
# ========================================

# Instancia global del asistente
asistente = AsistenteFisica()

# Crear un agente personalizado que herede de LlmAgent

class RAGAgent(LlmAgent):
    """Agente personalizado que integra el flujo RAG completo"""
    
    # Declarar asistente como un campo de Pydantic
    asistente: Any = None
    
    # Configurar el modelo para permitir tipos arbitrarios
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, asistente_instance, **kwargs):
        # Inicializar LlmAgent con configuración básica
        super().__init__(
            name="asistente_fisica_rag",
            model="gemini-2.5-flash",
            description="Asistente de Física I de la UBA con sistema RAG completo",
            instruction="""Eres un profesor experto en Física I de la Universidad de Buenos Aires.
Ayudas a los estudiantes con sus consultas sobre física usando un sistema RAG que busca en documentos del curso.""",
            asistente=asistente_instance,
            **kwargs
        )
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Método principal que procesa las consultas del usuario.
        Este método es llamado por el Runner de ADK.
        Sobrescribimos este método para usar nuestro flujo RAG personalizado.
        """
        try:
            # Procesar la consulta usando el flujo RAG completo
            respuesta = await self.asistente.iniciar_flujo(prompt, user_id="usuario_web")
            return respuesta
        except Exception as e:
            print(f"Error en RAGAgent.generate: {e}")
            import traceback
            traceback.print_exc()
            return f"Lo siento, hubo un error al procesar tu consulta. Por favor, intenta de nuevo."

# Crear el agente RAG personalizado
rag_agent = RAGAgent(asistente)

# Crear instancia de ADK con AG-UI
adk_fisica_agent = ADKAgent(
    adk_agent=rag_agent,
    app_name="fisica_uba_app",
    user_id="estudiante_fisica",
    session_timeout_seconds=7200,
    use_in_memory_services=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Iniciando Asistente de Física...")
    asistente.inicializar_componentes()

    # Procesar PDFs para extraer temario
    dir_pdf = os.getenv("DIR_PDF", "./pdfs")  # Usar variable de entorno o directorio por defecto
    archivos_pdf = []
    
    if os.path.exists(dir_pdf):
        archivos_pdf = [
            os.path.join(dir_pdf, f) 
            for f in os.listdir(dir_pdf) 
            if f.lower().endswith('.pdf')
        ]
        print(f"📁 Directorio de PDFs: {dir_pdf}")
        print(f"📚 Encontrados {len(archivos_pdf)} archivos PDF")
    else:
        print(f"⚠️ Directorio de PDFs no encontrado: {dir_pdf}")
    
    if archivos_pdf:
        asistente.procesar_pdfs_temario(archivos_pdf)
        await asistente.procesar_y_almacenar_pdfs(archivos_pdf)
    else:
        print("ℹ️ No se encontraron archivos PDF locales. Se usará la base de datos existente.")
        # Intentar recuperar temario de la base de datos o generar uno genérico
        # Por ahora dejamos que el flujo normal maneje esto
        
    yield
    # Shutdown
    print("👋 Apagando Asistente de Física...")

# Crear aplicación FastAPI
app = FastAPI(
    title="Asistente de Física I - UBA",
    description="Sistema RAG con agentes ADK para consultas de física",
    version="1.0.0",
    lifespan=lifespan
)

# Agregar el endpoint de ADK
add_adk_fastapi_endpoint(app, adk_fisica_agent, path="/")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "AsistenteFisica"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)