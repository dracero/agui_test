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

# ============================================================================
# CONFIGURACIÓN OFFICAL DE LANGSMITH (OPENTELEMETRY)
# ============================================================================
try:
    from langsmith.integrations.otel import configure
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    
    # Configurar trazado automático
    configure(
        project_name=os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT") or "agente_fisica_adk"
    )
    
    # Instrumentar ADK
    GoogleADKInstrumentor().instrument()
    
    from langsmith import traceable
    print("✅ LangSmith configurado con OpenTelemetry")
    LANGSMITH_ENABLED = True

except ImportError as e:
    print(f"⚠️ Error importando dependencias de OpenTelemetry: {e}")
    print("💡 Asegúrate de instalar: opentelemetry-sdk opentelemetry-exporter-otlp openinference-instrumentation-google-adk langsmith[otel]")
    LANGSMITH_ENABLED = False
    
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

# Imports de DSPy
import dspy
try:
    from .dspy_modules import RAGModule
except ImportError:
    # Fallback for when running directly
    from dspy_modules import RAGModule

# ============================================================================
# DECORADOR PERSONALIZADO PARA TODAS LAS ACCIONES
# ============================================================================
def medir_accion(nombre: str, tipo: str, extra_metadata: dict = None):
    """
    Decorador universal para medir todas las acciones del sistema.
    
    Args:
        nombre: Nombre de la acción para trazabilidad
        tipo: Tipo de acción (agente, busqueda, escritura_db, lectura_db, prompt, respuesta, procesamiento)
        extra_metadata: Diccionario con metadata adicional
    """
    def decorator(func):
        metadata = {
            "action_type": tipo,
            "function": func.__name__,
            "module": func.__module__
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        
        @traceable(name=nombre, run_type="chain", metadata=metadata)
        async def async_wrapper(*args, **kwargs):
            inicio = time.time()
            print(f"\n{'='*60}")
            print(f"🎯 ACCIÓN: {nombre} | TIPO: {tipo}")
            print(f"⏰ Inicio: {time.strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            try:
                # Loguear inputs (sin exponer API keys)
                inputs_log = {k: str(v)[:100] for k, v in kwargs.items() if not any(s in k.lower() for s in ['key', 'token', 'secret'])}
                if inputs_log:
                    print(f"📥 Inputs: {inputs_log}")
                
                result = await func(*args, **kwargs)
                
                tiempo = time.time() - inicio
                print(f"✅ Éxito | ⏱️ Tiempo: {tiempo:.2f}s")
                print(f"{'='*60}\n")
                
                return result
            
            except Exception as e:
                tiempo = time.time() - inicio
                print(f"❌ Error: {str(e)} | ⏱️ Tiempo: {tiempo:.2f}s")
                print(f"{'='*60}\n")
                raise
        
        @traceable(name=nombre, run_type="chain", metadata=metadata)
        def sync_wrapper(*args, **kwargs):
            inicio = time.time()
            print(f"\n{'='*60}")
            print(f"🎯 ACCIÓN: {nombre} | TIPO: {tipo}")
            print(f"⏰ Inicio: {time.strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            try:
                inputs_log = {k: str(v)[:100] for k, v in kwargs.items() if not any(s in k.lower() for s in ['key', 'token', 'secret'])}
                if inputs_log:
                    print(f"📥 Inputs: {inputs_log}")
                
                result = func(*args, **kwargs)
                
                tiempo = time.time() - inicio
                print(f"✅ Éxito | ⏱️ Tiempo: {tiempo:.2f}s")
                print(f"{'='*60}\n")
                
                return result
            
            except Exception as e:
                tiempo = time.time() - inicio
                print(f"❌ Error: {str(e)} | ⏱️ Tiempo: {tiempo:.2f}s")
                print(f"{'='*60}\n")
                raise
        
        # Retornar wrapper apropiado según tipo de función
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
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
    @medir_accion("agent_response", "agente")
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
                    result = response.text
                elif hasattr(response, 'content'):
                    result = response.content
                elif hasattr(response, 'message'):
                    result = response.message
                else:
                    result = str(response)
                
                # Actualizar contexto con la respuesta
                return result

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

        # 1. Configurar LLM para LangChain (para compatibilidad con memoria)
        self.llm = ChatGoogleGenerativeAI(**gemini_config)

        # 2. Configurar DSPy
        try:
            # Check if dspy.Google exists (compatibility)
            if hasattr(dspy, 'Google'):
                lm = dspy.Google("models/gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY"))
            else:
                lm = dspy.LM("models/gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY"))
            
            dspy.settings.configure(lm=lm)
            print(f"✅ DSPy configurado correctamente.")
        except Exception as e:
            print(f"❌ Error configurando DSPy: {e}")
            # No fallar completamente, permitir que el resto de componentes carguen
            # aunque el flujo GEPA podría fallar luego si se invoca.

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
        # Mantener legacy support si es necesario, aunque ya no se usa LlmAgent directamente para la lógica core
        if hasattr(self, 'classifier_agent'):
             self.runner = Runner(
                app_name="Asistente de Física",
                agent=self.classifier_agent,
                session_service=self.session_service
            )

        print("✅ Componentes ADK inicializados")

    def _crear_agentes(self):
        """Crear los módulos DSPy y agentes ADK de soporte."""
        
        # 1. Inicializar Módulo DSPy
        print("⚙️ Cargando módulo RAG optimizado con DSPy...")
        self.rag_module = RAGModule()
        
        # Intentar cargar pesos optimizados
        try:
            optimizer_path = os.path.join(os.path.dirname(__file__), "optimized_responder.json")
            if os.path.exists(optimizer_path):
                self.rag_module.responder.load(optimizer_path)
                print(f"✅ Pesos optimizados cargados desde {optimizer_path}")
            else:
                print("ℹ️ No se encontró 'optimized_responder.json', usando modelo base.")
        except Exception as e:
            print(f"⚠️ Error cargando pesos optimizados: {e}")

        # 2. Agentes ADK Legacy (Mantenidos para compatibilidad de estructura, pero lógica core movida a DSPy)
        # Esto asegura que si algún otro componente depende de self.classifier_agent, no rompa.
        self.classifier_agent = LlmAgent(
            name="clasificador",
            model="gemini-2.5-flash",
            description="Agente especializado en clasificar consultas de física",
            instruction="Legacy agent replaced by DSPy"
        )
        self.search_agent = LlmAgent(name="buscador", model="gemini-2.5-flash", instruction="Legacy")
        self.response_agent = LlmAgent(name="respondedor", model="gemini-2.5-flash", instruction="Legacy")

        self.agents = {
            'classifier': self.classifier_agent,
            'search': self.search_agent,
            'response': self.response_agent
        }
        print("✅ Agentes ADK (wrapper) y DSPy RAG Module creados")

    # --- NUEVOS MÉTODOS HELPERS PARA DSPY CON TRAZABILIDAD ---

    @medir_accion("dspy_clasificacion_busqueda", "agente", {"framework": "dspy"})
    def _run_dspy_classify_search(self, consultation, context, syllabus):
        """Ejecuta la clasificación y generación de búsqueda usando DSPy"""
        # DSPy espera inputs directos. El módulo RAGModule.forward maneja esto.
        return self.rag_module(
            user_query=consultation,
            memory_context=context,
            syllabus=syllabus
        )

    @medir_accion("dspy_generar_respuesta", "agente", {"framework": "dspy"})
    def _run_dspy_generate_response(self, consultation, context, classification, search_results):
        """Ejecuta la generación de respuesta usando DSPy"""
        return self.rag_module.generate_response(
            user_query=consultation,
            memory_context=context,
            classification=classification,
            retrieved_context=search_results
        )
    # ---------------------------------------------------------

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

    @medir_accion("procesar_temario", "procesamiento", {"formato": "pdf"})
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

    async def check_qdrant_has_data(self):
        """Verificar si la colección de Qdrant existe y tiene datos"""
        try:
            client = AsyncQdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
            collection_info = await client.get_collection(self.collection_name)
            points_count = collection_info.points_count
            print(f"ℹ️ Colección '{self.collection_name}' encontrada con {points_count} puntos")
            return points_count > 0
        except Exception as e:
            print(f"ℹ️ Colección '{self.collection_name}' no existe o no se puede acceder: {e}")
            return False

    @medir_accion("almacenar_pdfs_qdrant", "escritura_db", {"db": "qdrant"})
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

    @medir_accion("busqueda_qdrant", "lectura_db", {"db": "qdrant"})
    async def search_documents(self, query, top_k=5):
        """Realizar búsqueda en Qdrant"""
        try:
            # Actualizar contexto de Langfuse con la query
            
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

            for idx, result in enumerate(results):
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

    # Función de flujo corregida (GEPA Optimized)
    @medir_accion("flujo_adk_gepa", "pipeline", {"sistema": "dspy_gepa"})
    async def iniciar_flujo(self, consulta_usuario: str, user_id: str = "default_user"):
        """
        Iniciar el flujo completo de procesamiento usando DSPy (GEPA optimized).
        """
        print(f"📝 Consulta recibida de '{user_id}': {consulta_usuario}")
        
        trayectoria = []
        inicio_total = time.time()

        # Obtener contexto de memoria semántica
        contexto_memoria = self.memoria_semantica.get_context()

        try:
            # --- Paso 1: Clasificación y Generación de Búsqueda (DSPy) ---
            inicio_paso = time.time()

            # Usar el wrapper trazable para llamar a DSPy
            dspy_prediction = self._run_dspy_classify_search(
                consultation=consulta_usuario,
                context=contexto_memoria,
                syllabus=self.temario
            )

            clasificacion = dspy_prediction.classification
            consulta_busqueda = dspy_prediction.search_query
            
            tiempo_paso1 = time.time() - inicio_paso

            trayectoria.append({
                "paso": "clasificacion_busqueda",
                "clasificacion": clasificacion,
                "query_generada": consulta_busqueda,
                "tiempo": tiempo_paso1
            })
            
            print(f"✅ Clasificación DSPy completada en {tiempo_paso1:.2f}s")
            print(f"   Tipo: {clasificacion}")
            print(f"   Búsqueda generada: {consulta_busqueda}")


            # --- Paso 2: Realizar búsqueda en Qdrant (Existente) ---
            inicio_paso = time.time()
            resultados_busqueda = await self.search_documents(consulta_busqueda)
            
            # Formatear resultados para el prompt
            contexto_busqueda = "\n".join([
                f"--- Fragmento {i} (PDF: {res['pdf']}) ---\n{res['texto']}"
                for i, res in enumerate(resultados_busqueda, 1)
            ])
            
            tiempo_paso2 = time.time() - inicio_paso

            trayectoria.append({
                "paso": "busqueda_qdrant",
                "resultados": len(resultados_busqueda),
                "tiempo": tiempo_paso2
            })
            print(f"✅ Búsqueda en Qdrant completada en {tiempo_paso2:.2f}s")


            # --- Paso 3: Generar respuesta final (DSPy) ---
            inicio_paso = time.time()

            # Usar el wrapper trazable para generar respuesta
            respuesta_final = self._run_dspy_generate_response(
                consultation=consulta_usuario,
                context=contexto_memoria,
                classification=clasificacion,
                search_results=contexto_busqueda
            )

            tiempo_paso3 = time.time() - inicio_paso

            trayectoria.append({
                "paso": "generacion_respuesta",
                "respuesta_length": len(respuesta_final),
                "tiempo": tiempo_paso3
            })
            print(f"✅ Respuesta final generada en {tiempo_paso3:.2f}s")

            # Actualizar la memoria con la nueva interacción
            self.memoria_semantica.add_interaction(consulta_usuario, respuesta_final)

            tiempo_total = time.time() - inicio_total
            
            # Guardar la trayectoria (opcional)
            try:
                with open("trayectoria_gepa.json", "w", encoding="utf-8") as f:
                    json.dump(trayectoria, f, indent=4, ensure_ascii=False)
            except Exception:
                pass

            return respuesta_final

        except Exception as e:
            print(f"❌ Error en el flujo DSPy/GEPA: {e}")
            import traceback
            traceback.print_exc()

            # Devolver una respuesta de fallback
            return f"Lo siento, hubo un error técnico al procesar tu consulta. Por favor, intenta de nuevo."

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

    # Verificar si Qdrant ya tiene datos
    # Verificar si Qdrant ya tiene datos
    try:
        # has_data = await asistente.check_qdrant_has_data()
        # if has_data:
        #     print("✅ Qdrant ya contiene datos. (Verificando nuevos PDFs...)")

        dir_pdf = os.getenv("DIR_PDF", "./pdfs")
        archivos_pdf = []
        
        if os.path.exists(dir_pdf):
            archivos_pdf = [
                os.path.join(dir_pdf, f) 
                for f in os.listdir(dir_pdf) 
                if f.lower().endswith('.pdf')
            ]
        
        if archivos_pdf:
            try:
                print(f"📖 Procesando {len(archivos_pdf)} archivos PDF en '{dir_pdf}'...")
                asistente.procesar_pdfs_temario(archivos_pdf)
                await asistente.procesar_y_almacenar_pdfs(archivos_pdf)
                print("✅ PDFs procesados y cargados exitosamente (Sobrescribiendo/Actualizando)")
            except Exception as e:
                print(f"❌ Error al procesar PDFs: {e}")
                import traceback
                traceback.print_exc()
                if not asistente.temario:
                    asistente.temario = "Física I - UBA (Error al cargar PDFs)"
        else:
            print(f"ℹ️ No se encontraron archivos PDF en '{dir_pdf}'. Se usará conocimiento existente en Qdrant o del modelo.")
            try:
                has_data = await asistente.check_qdrant_has_data()
                if has_data:
                    # Intentar cargar temario de metadatos o generarlo genérico
                    asistente.temario = "Física I - UBA (Datos en Qdrant)"
                    print("✅ Se detectaron datos previos en Qdrant.")
                else:
                    asistente.temario = "Física I - UBA (Sin datos)"
            except:
                pass
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        # Continuar de todos modos
        asistente.temario = "Física I - UBA"
    
    print("✅ Backend listo y escuchando en el puerto configurado")
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