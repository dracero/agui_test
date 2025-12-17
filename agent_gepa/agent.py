"""Asistente de Física I - UBA con AG-UI y ADK (Versión Optimizada con DSPy GEPA)"""

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
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, MultiVectorConfig, MultiVectorComparator
from transformers import AutoTokenizer, AutoModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document

# Imports de Google ADK
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from pydantic import BaseModel, ConfigDict
from google.genai import types, Client

# Imports de DSPy
import dspy
try:
    from .dspy_modules import RAGModule
except ImportError:
    from dspy_modules import RAGModule

# Imports for Custom Embeddings
from typing import List
from fastembed import LateInteractionTextEmbedding
from langchain_core.embeddings import Embeddings

class FastEmbedColbertEmbeddings(Embeddings):
    """
    Custom Embeddings class for Late Interaction (ColBERT) models using FastEmbed.
    Generates multi-vector embeddings.
    """
    def __init__(self, model_name: str = "colbert-ir/colbertv2.0", batch_size: int = 32):
        self.model = LateInteractionTextEmbedding(model_name=model_name)
        self.batch_size = batch_size

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed documents. Returns a list of multivectors.
        Note: FastEmbed returns generators, we iterate to consume them.
        Each document embedding is a list of vectors (float lists).
        """
        embeddings_generator = self.model.embed(texts, batch_size=self.batch_size)
        return [list(emb) for emb in embeddings_generator]

    def embed_query(self, text: str) -> List[float]:
        """
        Embed query. Returns a multivector for the query.
        """
        embedding_generator = self.model.query_embed(text)
        return list(next(embedding_generator))

# ============================================================================
# CONFIGURACIÓN DE LANGSMITH (TELEMETRÍA)
# ============================================================================
def setup_langsmith_environment():
    """Configurar variables de entorno para LangSmith según el patrón correcto."""
    
    langsmith_config = {
        "LANGCHAIN_TRACING_V2": "true",
        "LANGCHAIN_API_KEY": os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY"),
        "LANGCHAIN_ENDPOINT": "https://api.smith.langchain.com",
        "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT") or "fisica-un-bot"
    }
    
    for key, value in langsmith_config.items():
        if value:
            os.environ[key] = value
    
    try:
        from langsmith import traceable, Client
        
        client = Client()
        
        return True, traceable, client
    
    except Exception as e:
        
        def dummy_traceable(*args, **kwargs):
            def decorator(func):
                return func
            if len(args) == 1 and callable(args[0]):
                return args[0]
            return decorator
        
        return False, dummy_traceable, None

# Configurar LangSmith al importar
LANGSMITH_ENABLED, traceable, langsmith_client = setup_langsmith_environment()

# Intentar instrumentar ADK si está disponible
try:
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    GoogleADKInstrumentor().instrument()
except ImportError:
    pass

# Aplicar nest_asyncio para permitir loops anidados
nest_asyncio.apply()

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
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                raise
        
        @traceable(name=nombre, run_type="chain", metadata=metadata)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                raise
        
        # Retornar wrapper apropiado según tipo de función
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator



class AsistenteFisica:
    """Clase unificada para el asistente de física con procesamiento de PDFs, RAG y memoria semántica usando Google ADK y DSPy GEPA"""

    def __init__(self):
        self._setup_apis()

        self.llm = None
        self.rag_module = None
        self.memoria_semantica = None
        self.agents = {}
        self.session_service = None
        self.runner = None
        self.temario = ""
        self.contenido_completo = ""

        self.model_name = "Qdrant/colbert-ir/colbertv2.0"
        self.embeddings = None

        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_KEY")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "documentos_pdf")

        self.classifier_agent = None
        self.search_agent = None
        self.response_agent = None
        
        # Cliente Qdrant reutilizable para optimizar conexiones
        self._qdrant_client = None
        self._qdrant_vectorstore = None
        
        # Estadísticas de tokens
        self.token_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "requests": []
        }

    def _setup_apis(self):
        """Configurar las APIs necesarias"""
        pass  # Configuración silenciosa
    
    def _get_qdrant_client(self):
        """Obtener cliente Qdrant reutilizable"""
        if self._qdrant_client is None:
            self._qdrant_client = QdrantClient(
                url=self.qdrant_url, 
                api_key=self.qdrant_api_key, 
                check_compatibility=False,
                timeout=60  # Aumentar timeout por defecto
            )
        return self._qdrant_client
    
    def _get_vectorstore(self):
        """Obtener vectorstore reutilizable"""
        if self._qdrant_vectorstore is None:
            self._qdrant_vectorstore = QdrantVectorStore(
                client=self._get_qdrant_client(),
                collection_name=self.collection_name,
                embedding=self.embeddings,
            )
        return self._qdrant_vectorstore
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimar tokens de un texto (aprox 1 token = 4 chars en español)"""
        if not text:
            return 0
        return len(text) // 4
    
    def _log_token_usage(self, paso: str, input_text: str, output_text: str, modelo: str = "gemini-2.5-flash"):
        """Registrar y mostrar uso de tokens"""
        input_tokens = self._estimate_tokens(input_text)
        output_tokens = self._estimate_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        
        self.token_stats["total_input_tokens"] += input_tokens
        self.token_stats["total_output_tokens"] += output_tokens
        self.token_stats["requests"].append({
            "paso": paso,
            "modelo": modelo,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        })
        
        return {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens}
    
    async def _call_llm_traced(self, agent_name: str, system_prompt: str, user_prompt: str) -> dict:
        """
        Llamar al LLM con tracing completo para LangSmith.
        Retorna la respuesta y metadata de tokens.
        """
        # Wrapper interno con traceable dinámico para capturar el nombre del agente
        @traceable(
            name=f"llm_call_{agent_name}", 
            run_type="llm",
            metadata={
                "agent_name": agent_name,
                "model": "gemini-2.5-flash",
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt)
            }
        )
        async def _traced_invoke(system_msg: str, user_msg: str) -> dict:
            messages = [
                SystemMessage(content=system_msg),
                HumanMessage(content=user_msg)
            ]
            return await self.llm.ainvoke(messages)
        
        # Llamar al LLM con tracing (automáticamente anidado en el parent trace)
        response = await _traced_invoke(system_prompt, user_prompt)
        
        # Extraer información de tokens si está disponible
        token_usage = {}
        if hasattr(response, 'response_metadata') and response.response_metadata:
            usage = response.response_metadata.get('usage_metadata', {})
            token_usage = {
                "input_tokens": usage.get('prompt_token_count', 0) or usage.get('input_tokens', 0),
                "output_tokens": usage.get('candidates_token_count', 0) or usage.get('output_tokens', 0),
                "total_tokens": usage.get('total_token_count', 0) or usage.get('total_tokens', 0)
            }
        
        # Si no hay metadata, estimar
        if not token_usage.get('total_tokens'):
            token_usage = {
                "input_tokens": self._estimate_tokens(system_prompt + user_prompt),
                "output_tokens": self._estimate_tokens(response.content),
                "total_tokens": self._estimate_tokens(system_prompt + user_prompt + response.content)
            }
        
        # Actualizar estadísticas
        self.token_stats["total_input_tokens"] += token_usage["input_tokens"]
        self.token_stats["total_output_tokens"] += token_usage["output_tokens"]
        self.token_stats["requests"].append({
            "paso": agent_name,
            "modelo": "gemini-2.5-flash",
            **token_usage
        })
        

        
        return {
            "content": response.content,
            "token_usage": token_usage,
            "model": "gemini-2.5-flash"
        }

    def inicializar_componentes(self):
        """Inicializar todos los componentes del asistente"""
        self._inicializar_modelos()
        self._inicializar_memoria()
        self._inicializar_adk()
        self._inicializar_modelo_embedding()

    def _inicializar_modelos(self):
        """Inicializar los modelos de lenguaje (DSPy y LangChain)"""
        gemini_config = {
            "model": "gemini-2.5-flash",  # CORREGIDO: modelo correcto
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "temperature": 0,
            "max_output_tokens": None,
        }

        self.llm = ChatGoogleGenerativeAI(**gemini_config)

        lm = dspy.LM(model="gemini/gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))
        dspy.settings.configure(lm=lm)

    def _inicializar_memoria(self):
        """Inicializar la memoria semántica"""
        self.memoria_semantica = self.SemanticMemory(llm=self.llm)

    class SemanticMemory:
        def __init__(self, llm, max_entries=10):
            self.llm = llm
            self.conversations = []
            self.max_entries = max_entries
            self.summary = ""
            self.direct_history = ""
            self.message_history = ChatMessageHistory()
            
        def add_interaction(self, query, response):
            """Añadir interacción a la memoria"""
            self.message_history.add_user_message(query)
            self.message_history.add_ai_message(response)
            
            self.conversations.append({"query": query, "response": response})
            
            if len(self.conversations) > self.max_entries:
                self.conversations.pop(0)
            
            recent_convs = self.conversations[-3:]
            self.direct_history = ""
            for conv in recent_convs:
                self.direct_history += f"\nUsuario: {conv['query']}\nAsistente: {conv['response']}\n"
            
            self.update_summary()

        def update_summary(self):
            """Actualizar resumen de la conversación manualmente"""
            try:
                messages = self.message_history.messages
                
                if len(messages) > 6:
                    old_messages = messages[:-6]
                    recent_messages = messages[-6:]
                    
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
                    
                    recent_text = "\n".join([
                        f"{'Usuario' if msg.type == 'human' else 'Asistente'}: {msg.content}"
                        for msg in recent_messages
                    ])
                    
                    self.summary = f"Resumen: {summary_text}\n\nRecientes:\n{recent_text}"
                else:
                    self.summary = f"Interacciones recientes:{self.direct_history}"
                    
            except Exception as e:
                self.summary = f"Interacciones recientes:{self.direct_history}"

        def get_context(self):
            """Obtener contexto actual de la conversación"""
            return self.summary if self.summary.strip() else "No hay conversación previa."

    def _inicializar_adk(self):
        """Inicializar componentes ADK"""
        self.session_service = InMemorySessionService()
        self._crear_agentes()

    def _dspy_to_instruction(self, predictor, description_override=None):
        """
        Extrae la instrucción y los ejemplos (demos) de un predictor DSPy
        para usarlos como instrucción de un agente ADK.
        """
        signature = None
        if hasattr(predictor, "signature"):
            signature = predictor.signature
        elif hasattr(predictor, "predictor") and hasattr(predictor.predictor, "signature"):
            signature = predictor.predictor.signature
            
        if not signature:
            return description_override or "Eres un asistente útil."
        
        instruction = signature.__doc__ if signature.__doc__ else "Eres un asistente útil."
        
        if hasattr(predictor, "extended_signature") and hasattr(predictor.extended_signature, "instructions"):
            instruction = predictor.extended_signature.instructions
            
        demos_text = ""
        demos = getattr(predictor, "demos", [])
        if not demos and hasattr(predictor, "predictor"):
            demos = getattr(predictor.predictor, "demos", [])
            
        if demos:
            demos_text = "\n\nEJEMPLOS DE COMPORTAMIENTO (FEW-SHOT):\n"
            for i, demo in enumerate(demos):
                demos_text += f"\n--- Ejemplo {i+1} ---\n"
                for field_name in signature.input_fields:
                    if field_name in demo:
                        demos_text += f"{field_name.upper()}: {demo[field_name]}\n"
                
                for field_name in signature.output_fields:
                    if field_name in demo:
                        demos_text += f"{field_name.upper()}: {demo[field_name]}\n"
                        
        full_instruction = f"{instruction}{demos_text}"
        return full_instruction

    def _crear_agentes(self):
        """Crear los agentes ADK utilizando las optimizaciones de DSPy."""
        
        self.rag_module = RAGModule()
        optimization_file = "optimized_responder.json"
        
        if os.path.exists(optimization_file):
            try:
                self.rag_module.responder.load(optimization_file)
            except Exception as e:
                pass
        
        instruction_classifier = self._dspy_to_instruction(self.rag_module.classifier)
        instruction_searcher = self._dspy_to_instruction(self.rag_module.search_generator)
        instruction_responder = self._dspy_to_instruction(self.rag_module.responder)
        
        self.classifier_agent = LlmAgent(
            name="clasificador",
            model="gemini-2.5-flash",  # CORREGIDO
            description="Agente especializado en clasificar consultas de física.",
            instruction=instruction_classifier
        )

        self.search_agent = LlmAgent(
            name="buscador",
            model="gemini-2.5-flash",  # CORREGIDO
            description="Agente que genera consultas de búsqueda optimizadas.",
            instruction=instruction_searcher
        )

        self.response_agent = LlmAgent(
            name="respondedor",
            model="gemini-2.5-flash",  # CORREGIDO
            description="Profesor experto en física que responde consultas.",
            instruction=instruction_responder
        )

        self.agents = {
            'classifier': self.classifier_agent,
            'search': self.search_agent,
            'response': self.response_agent
        }


    def _inicializar_modelo_embedding(self):
        """Inicializar el modelo de embeddings con batch_size optimizado"""
        # Usar Custom FastEmbedColbertEmbeddings para Late Interaction support
        self.embeddings = FastEmbedColbertEmbeddings(
            model_name="colbert-ir/colbertv2.0",
            batch_size=32,
        )

    def leer_pdf(self, nombre_archivo):
        """Leer contenido de un archivo PDF"""
        try:
            reader = PdfReader(nombre_archivo)
            return "".join(page.extract_text() for page in reader.pages)
        except Exception as e:
            return ""

    @medir_accion("procesar_temario", "procesamiento", {"formato": "pdf"})
    async def procesar_pdfs_temario(self, archivos_pdf):
        """Procesar PDFs para extraer el temario con tracing de tokens"""
        contenido_completo = ""

        for archivo in archivos_pdf:
            if os.path.exists(archivo):
                contenido_completo += f"\n--- Contenido de {archivo} ---\n"
                contenido_completo += self.leer_pdf(archivo)
        
        if not contenido_completo:
            return "Temario no disponible localmente. Se usará información de la base de datos."

        self.contenido_completo = contenido_completo

        cache_file = "temario.txt"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    self.temario = f.read()
                print(f"📚 Temario cargado desde cache ({cache_file})")
                return self.temario
            except Exception as e:
                pass

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

        # Usar _call_llm_traced para mostrar tokens y registrar en LangSmith
        print(f"\n{'='*60}")
        print(f"📖 GENERANDO TEMARIO - Llamada a LLM")
        print(f"{'='*60}")
        
        result = await self._call_llm_traced(
            agent_name="generador_temario",
            system_prompt=system_message,
            user_prompt=user_question
        )
        
        self.temario = result["content"]
        token_usage = result["token_usage"]
        
        print(f"\n📊 TOKENS [Generador Temario]")
        print(f"   ├─ Input:  {token_usage['input_tokens']:,} tokens")
        print(f"   ├─ Output: {token_usage['output_tokens']:,} tokens")
        print(f"   └─ Total:  {token_usage['total_tokens']:,} tokens")
        print(f"{'='*60}\n")

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(self.temario)
            print(f"✅ Temario guardado en cache ({cache_file})")
        except Exception as e:
            pass

        return self.temario

    def split_into_chunks(self, text, chunk_size=600, overlap=100):
        """Dividir texto en chunks con overlap para mejorar similaridad"""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunks.append(text[start:end])
            start += chunk_size - overlap  # Avanzar con overlap
            
            # Evitar chunks muy pequeños al final
            if text_len - start < overlap:
                break
        
        return chunks

    async def check_qdrant_has_data(self):
        """Verificar si la colección de Qdrant existe y tiene datos"""
        try:
            client = self._get_qdrant_client()
            collection_info = client.get_collection(self.collection_name)
            points_count = collection_info.points_count
            return points_count > 0
        except Exception as e:
            return False

    def clear_qdrant_collection(self):
        """Limpiar la colección de Qdrant para re-indexar conn ColBERT/MUVERA"""
        print(f"🧹 Iniciando limpieza de colección Qdrant (MUVERA): {self.collection_name}")
        try:
            client = self._get_qdrant_client()
            
            # Verificar si existe antes
            collections = client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            print(f"   Colección existe actualmente: {exists}")

            # Intentar borrar la colección existente
            try:
                client.delete_collection(self.collection_name)
                print(f"   🗑️ Colección eliminada: {self.collection_name}")
            except Exception as e:
                print(f"   ⚠️ No se pudo eliminar colección (quizás no existía): {e}")
            
            # Recrear la colección configurada para ColBERT (Multi-Vector)
            # ColBERT usa vectores de dimensión 128 y requiere MultiVectorConfig
            print(f"   ✨ Creando nueva colección Multi-Vector (ColBERT) con dimensión 128...")
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=128, 
                    distance=Distance.COSINE,
                    multivector_config=MultiVectorConfig(
                        comparator=MultiVectorComparator.MAX_SIM
                    )
                )
            )
            print(f"   ✅ Colección recreada exitosamente para ColBERT")
            
            # Invalidar caches
            self._qdrant_vectorstore = None
            
        except Exception as e:
            print(f"❌ Error CRÍTICO recreando colección: {e}")
            import traceback
            traceback.print_exc()

    @medir_accion("almacenar_pdfs_qdrant", "escritura_db", {"db": "qdrant"})
    async def procesar_y_almacenar_pdfs(self, pdf_files, force_reindex=True):
        """Procesar PDFs y almacenar en Qdrant usando multivectores (ColBERT) manualmente"""
        
        # Si force_reindex, limpiar la colección primero
        if force_reindex:
            self.clear_qdrant_collection()
        
        documents = []
        texts = []
        metadatas = []
        
        global_id_counter = 0

        for pdf_file in pdf_files:
            if not os.path.exists(pdf_file):
                continue

            text = self.leer_pdf(pdf_file)
            if text:
                chunks = self.split_into_chunks(text)
                for i, chunk in enumerate(chunks):
                    meta = {
                        "pdf_name": pdf_file,
                        "chunk_id": i,
                        "global_id": global_id_counter,
                        "text": chunk
                    }
                    metadatas.append(meta)
                    texts.append(chunk)
                    global_id_counter += 1

        if not texts:
            return

        client = self._get_qdrant_client()
        
        print(f"⚡ Generando embeddings ColBERT para {len(texts)} chunks...")
        # Generar embeddings usando nuestra clase custom (devuelve lista de listas de float)
        # embed_documents devuelve List[List[List[float]]] -> [Doc1Multivector, Doc2Multivector...]
        multivectors_list = self.embeddings.embed_documents(texts)
        
        points = []
        for idx, (multivector, meta) in enumerate(zip(multivectors_list, metadatas)):
            # Qdrant espera PointStruct con vector=multivector (List[List[float]])
            points.append(PointStruct(
                id=idx,
                vector=multivector,
                payload=meta
            ))
            
        print(f"💾 Subiendo {len(points)} puntos a Qdrant...")
        # Subir en lotes para evitar timeout (ColBERT multivectors son pesados)
        batch_size = 10  # Reducido de 50 a 10 para evitar timeouts
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            try:
                client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            except Exception as e:
                print(f"⚠️ Error subiendo lote {i}: {e}")
                # Reintentar una vez con delay
                import time
                time.sleep(2)
                client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
        print(f"✅ Almacenamiento completado en colección {self.collection_name}")
        
        # Invalidar cache del vectorstore (aunque ya no lo usamos para esto, por consistencia)
        self._qdrant_vectorstore = None

    @medir_accion("busqueda_qdrant", "lectura_db", {"db": "qdrant", "tipo": "vector_search"})
    async def search_documents(self, query, top_k=5):
        """Realizar búsqueda en Qdrant usando ColBERT y cliente directo"""
        try:
            client = self._get_qdrant_client()
            
            # Generar embedding para la query
            # embed_query devuelve List[float] (flattened? No, nuestra clase devuelve List[float] pero ColBERT query es multivector)
            # Espera, embed_query en nuestra clase hace:
            # embedding_generator = self.model.query_embed(text)
            # return list(next(embedding_generator))
            # Eso devuelve un multivector (lista de vectores), PERO la firma de Embeddings dice List[float].
            # Aquí lo llamaremos directo si es posible, o usamos el resultado sabiendo que es una lista de listas.
            
            # Generamos el query vector (multivector)
            query_vector = self.embeddings.embed_query(query)
            # query_vector es List[List[float]] realmente, aunque type hint diga List[float]
            
            # Búsqueda usando query_points (necesario para search multivector eficiente)
            search_result = client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k
            ).points
            
            # Adaptamos para que el resto del código lo entienda como (doc, score)
            results = []
            for point in search_result:
                # Reconstruir objeto Document simulado
                payload = point.payload or {}
                content = payload.get("text", "")
                # Eliminamos 'text' del metadata para no duplicarlo
                metadata = {k:v for k,v in payload.items() if k != 'text'}
                
                doc = Document(page_content=content, metadata=metadata)
                score = point.score
                results.append((doc, score))

            # Formatear resultados con información completa para el tracer
            formatted_results = []
            documents_for_trace = []
            
            for idx, (doc, score) in enumerate(results):
                # Con ColBERT/MUVERA y Qdrant, el score es MaxSim (suma de similitudes máximas)
                # No es una distancia, y puede ser mayor a 1.
                # Cuanto mayor, más similar.
                similarity = score
                
                doc_info = {
                    "pdf": doc.metadata.get("pdf_name", "N/A"),
                    "texto": doc.page_content,
                    "similitud": round(similarity, 4),
                    "score_colbert": round(score, 4)
                }
                formatted_results.append(doc_info)
                
                # Información detallada para el tracer
                # Información detallada para el tracer
                documents_for_trace.append({
                    "rank": idx + 1,
                    "source": doc.metadata.get("pdf_name", "N/A"),
                    "chunk_id": doc.metadata.get("chunk_id", "N/A"),
                    "similarity_score": round(similarity, 4),
                    "colbert_score": round(score, 4),  # Score original (MaxSim)
                    "content_preview": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    "content_length": len(doc.page_content)
                })
            
            # Retorno estructurado para LangSmith (el tracer captura automáticamente el return)
            return {
                "query": query,
                "top_k": top_k,
                "num_results": len(formatted_results),
                "documents": documents_for_trace,
                "results": formatted_results
            }

        except Exception as e:
            error_msg = f"Error en la búsqueda: {str(e)}"
            return {
                "query": query,
                "top_k": top_k,
                "num_results": 0,
                "documents": [],
                "results": [{"pdf": "Error", "texto": error_msg, "similitud": 0}],
                "error": error_msg
            }

    @medir_accion("ejecutar_agente_adk", "agente_adk")
    async def _get_agent_response(self, agent, input_data):
        """
        Función auxiliar para obtener respuesta de un agente.
        Usa LangChain directamente con tracing para LangSmith.
        """
        try:
            if isinstance(input_data, dict):
                prompt = self._format_prompt_for_agent(agent.name, input_data)
            else:
                prompt = str(input_data)

            # Obtener instrucción del agente
            system_prompt = getattr(agent, 'instruction', 'Eres un asistente de física experto.')
            
            # Usar LangChain con tracing completo para LangSmith
            result = await self._call_llm_traced(
                agent_name=agent.name,
                system_prompt=system_prompt,
                user_prompt=prompt
            )
            
            return result["content"]

        except Exception as e:
            import traceback
            traceback.print_exc()
            
            # Fallback sin tracing
            try:
                if isinstance(input_data, dict):
                    prompt = self._format_prompt_for_agent(agent.name, input_data)
                else:
                    prompt = str(input_data)
                    
                messages = [
                    SystemMessage(content=getattr(agent, 'instruction', 'Eres un asistente de física experto.')),
                    HumanMessage(content=prompt)
                ]
                response = await self.llm.ainvoke(messages)
                return response.content
            except Exception as fallback_error:
                return f"Error procesando con {agent.name}"

    def _format_prompt_for_agent(self, agent_name, data):
        """Formatear el prompt según el agente específico y la firma DSPy esperada"""
        if agent_name == "clasificador":
            return f"""
SYLLABUS:
{data.get('syllabus', '')}

MEMORY_CONTEXT:
{data.get('memory_context', '')}

USER_QUERY:
{data.get('user_query', '')}

Classify this query.
"""
        elif agent_name == "buscador":
            return f"""
CLASSIFICATION:
{data.get('classification', '')}

ORIGINAL_QUERY:
{data.get('original_query', '')}

MEMORY_CONTEXT:
{data.get('memory_context', '')}

Generate search query.
"""
        elif agent_name == "respondedor":
            return f"""
USER_QUERY:
{data.get('user_query', '')}

MEMORY_CONTEXT:
{data.get('memory_context', '')}

CLASSIFICATION:
{data.get('classification', '')}

RETRIEVED_CONTEXT:
{data.get('retrieved_context', '')}

Generate response.
"""
        return str(data)

    @medir_accion("flujo_adk_completo", "pipeline", {"sistema": "adk_dspy_gepa"})
    async def iniciar_flujo(self, consulta_usuario: str, user_id: str = "default_user"):
        """
        Flujo completo usando AGENTES ADK con trazabilidad detallada
        """
        trayectoria = []
        inicio_total = time.time()
        contexto_memoria = self.memoria_semantica.get_context()

        try:
            # PASO 1: CLASIFICADOR
            inicio_paso = time.time()
            
            clasificacion_data = {
                "syllabus": self.temario,
                "memory_context": contexto_memoria,
                "user_query": consulta_usuario
            }
            
            clasificacion_raw = await self._get_agent_response(
                agent=self.classifier_agent,
                input_data=clasificacion_data
            )
            
            # Asegurar que clasificacion_raw no sea None
            if not clasificacion_raw:
                clasificacion_raw = "Clasificación no disponible - usando consulta original"
            
            tiempo_clasificacion = time.time() - inicio_paso
            
            trayectoria.append({
                "paso": 1,
                "agente": "classifier_agent",
                "agente_tipo": "LlmAgent_ADK",
                "modelo": "gemini-2.5-flash",
                "input": {
                    "user_query": consulta_usuario[:100] + ("..." if len(consulta_usuario) > 100 else ""),
                    "has_memory": bool(contexto_memoria),
                    "has_syllabus": bool(self.temario),
                    "syllabus_length": len(self.temario) if self.temario else 0
                },
                "output": {
                    "classification": str(clasificacion_raw)[:200] + ("..." if len(str(clasificacion_raw)) > 200 else ""),
                    "output_length": len(str(clasificacion_raw)) if clasificacion_raw else 0
                },
                "tiempo_segundos": round(tiempo_clasificacion, 3),
                "timestamp": time.strftime('%H:%M:%S')
            })
            
            # Registrar tokens del clasificador
            input_text_1 = self._format_prompt_for_agent("clasificador", clasificacion_data)
            self._log_token_usage("Clasificador", input_text_1, str(clasificacion_raw))

            # PASO 2: GENERADOR DE BÚSQUEDA
            inicio_paso = time.time()
            
            search_data = {
                "classification": clasificacion_raw,
                "original_query": consulta_usuario,
                "memory_context": contexto_memoria
            }
            
            consulta_busqueda = await self._get_agent_response(
                agent=self.search_agent,
                input_data=search_data
            )
            
            tiempo_query = time.time() - inicio_paso
            
            trayectoria.append({
                "paso": 2,
                "agente": "search_agent",
                "agente_tipo": "LlmAgent_ADK",
                "modelo": "gemini-2.5-flash",
                "input": {
                    "classification": str(clasificacion_raw)[:100] + ("..." if len(str(clasificacion_raw)) > 100 else ""),
                    "original_query": consulta_usuario[:100] + ("..." if len(consulta_usuario) > 100 else "")
                },
                "output": {
                    "search_query": consulta_busqueda,
                    "query_length": len(consulta_busqueda) if consulta_busqueda else 0
                },
                "tiempo_segundos": round(tiempo_query, 3),
                "timestamp": time.strftime('%H:%M:%S')
            })
            
            # Registrar tokens del buscador
            input_text_2 = self._format_prompt_for_agent("buscador", search_data)
            self._log_token_usage("Buscador", input_text_2, str(consulta_busqueda))

            # PASO 3: BÚSQUEDA EN QDRANT
            inicio_paso = time.time()
            
            # Limpiar query (manejo de nulos seguro)
            clean_query = (consulta_busqueda or "").replace('Search Query:', '').replace('"', '').strip()
            search_response = await self.search_documents(clean_query)
            
            # Extraer resultados del nuevo formato estructurado
            resultados_busqueda = search_response.get("results", [])
            documents_trace = search_response.get("documents", [])
            
            tiempo_busqueda = time.time() - inicio_paso
            
            trayectoria.append({
                "paso": 3,
                "agente": "qdrant_retriever",
                "agente_tipo": "VectorStore",
                "database": "Qdrant",
                "input": {
                    "query": clean_query,
                    "top_k": 5
                },
                "output": {
                    "num_docs": len(resultados_busqueda),
                    "documents_retrieved": documents_trace
                },
                "tiempo_segundos": round(tiempo_busqueda, 3),
                "timestamp": time.strftime('%H:%M:%S')
            })

            # PASO 4: RESPONDEDOR
            inicio_paso = time.time()
            
            contexto_busqueda = "\n".join([
                f"--- Fragmento (PDF: {res['pdf']}) ---\n{res['texto']}"
                for res in resultados_busqueda
            ])
            
            response_data = {
                "user_query": consulta_usuario,
                "memory_context": contexto_memoria,
                "classification": clasificacion_raw,
                "retrieved_context": contexto_busqueda
            }
            
            respuesta_final = await self._get_agent_response(
                agent=self.response_agent,
                input_data=response_data
            )
            
            tiempo_respuesta = time.time() - inicio_paso
        
            trayectoria.append({
                "paso": 4,
                "agente": "response_agent",
                "agente_tipo": "LlmAgent_ADK",
                "modelo": "gemini-2.5-flash",
                "input": {
                    "user_query": consulta_usuario[:100] + ("..." if len(consulta_usuario) > 100 else ""),
                    "num_docs_context": len(resultados_busqueda),
                    "context_length": len(contexto_busqueda)
                },
                "output": {
                    "response_preview": str(respuesta_final)[:200] + ("..." if len(str(respuesta_final)) > 200 else ""),
                    "response_length": len(respuesta_final) if respuesta_final else 0
                },
                "tiempo_segundos": round(tiempo_respuesta, 3),
                "timestamp": time.strftime('%H:%M:%S')
            })
            
            # Registrar tokens del respondedor
            input_text_4 = self._format_prompt_for_agent("respondedor", response_data)
            self._log_token_usage("Respondedor", input_text_4, str(respuesta_final))

            self.memoria_semantica.add_interaction(consulta_usuario, respuesta_final)
            
            tiempo_total = time.time() - inicio_total
            
            trayectoria_completa = {
                "metadata": {
                    "user_id": user_id,
                    "query": consulta_usuario,
                    "tiempo_total_segundos": round(tiempo_total, 3),
                    "num_pasos": len(trayectoria),
                    "timestamp_inicio": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "sistema": "ADK + DSPy GEPA",
                    "version": "2.0.0"
                },
                "pasos": trayectoria,
                "resumen": {
                    "clasificacion": str(clasificacion_raw)[:100],
                    "query_busqueda": consulta_busqueda,
                    "num_docs_recuperados": len(resultados_busqueda),
                    "respuesta_length": len(respuesta_final) if respuesta_final else 0
                }
            }
            
            try:
                with open("trayectoria_adk_completa.json", "w", encoding="utf-8") as f:
                    json.dump(trayectoria_completa, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

            return respuesta_final

        except Exception as e:
            import traceback
            traceback.print_exc()
            
            try:
                with open("trayectoria_adk_error.json", "w", encoding="utf-8") as f:
                    json.dump({
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        "pasos_completados": trayectoria,
                        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                    }, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
            
            return f"Lo siento, hubo un error técnico: {str(e)}"


# ========================================
# CONFIGURACIÓN DE AG-UI y FASTAPI
# ========================================

asistente = AsistenteFisica()

class RAGAgent(LlmAgent):
    """Agente personalizado que integra el flujo RAG completo con DSPy GEPA"""
    asistente: Any = None
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, asistente_instance, **kwargs):
        super().__init__(
            name="asistente_fisica_gepa",
            model="gemini-2.5-flash",  # CORREGIDO
            description="Asistente de Física I de la UBA con sistema RAG optimizado con DSPy GEPA",
            instruction="""Eres un profesor experto en Física I de la Universidad de Buenos Aires.""",
            asistente=asistente_instance,
            **kwargs
        )
    
    @traceable(name="chat_consulta_usuario", run_type="chain", metadata={"source": "web_ui", "sistema": "rag_gepa"})
    async def generate(self, prompt: str, **kwargs) -> str:
        """Método principal que procesa las consultas del usuario"""
        try:
            respuesta = await self.asistente.iniciar_flujo(prompt, user_id="usuario_web")
            return respuesta
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Lo siento, hubo un error al procesar tu consulta."

rag_agent = RAGAgent(asistente)

adk_fisica_agent = ADKAgent(
    adk_agent=rag_agent,
    app_name="fisica_uba_app_gepa",
    user_id="estudiante_fisica",
    session_timeout_seconds=7200,
    use_in_memory_services=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    asistente.inicializar_componentes()
    
    try:
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
                await asistente.procesar_pdfs_temario(archivos_pdf)
                
                # Verificar si ya existen datos en Qdrant para evitar re-indexación innecesaria
                has_data = await asistente.check_qdrant_has_data()
                if not has_data:
                    print("📂 Procesando PDFs e indexando en Qdrant...")
                    await asistente.procesar_y_almacenar_pdfs(archivos_pdf, force_reindex=True)
                else:
                    print("✅ Datos encontrados en Qdrant. Omitiendo re-indexación automática.")
            except Exception as e:
                import traceback
                traceback.print_exc()
                if not asistente.temario:
                    asistente.temario = "Física I - UBA (Error al cargar PDFs)"
        else:
            try:
                has_data = await asistente.check_qdrant_has_data()
                if has_data:
                    asistente.temario = "Física I - UBA (Datos en Qdrant)"
                else:
                    asistente.temario = "Física I - UBA (Sin datos)"
            except:
                pass

    except Exception as e:
        import traceback
        traceback.print_exc()
        asistente.temario = "Física I - UBA"
    
    yield

app = FastAPI(
    title="Asistente de Física I - GEPA",
    description="Sistema RAG con optimización DSPy GEPA",
    version="2.0.0",
    lifespan=lifespan
)

# ============================================================================
# ENDPOINT PERSONALIZADO PARA AG-UI CON TRACING COMPLETO
# ============================================================================
from fastapi import Request
from fastapi.responses import StreamingResponse
import uuid

class ChatRequest(BaseModel):
    """Modelo para solicitudes de chat"""
    message: str
    user_id: str = "default_user"
    session_id: str = None

@app.post("/")
async def chat_endpoint(request: Request):
    """
    Endpoint principal compatible con AG-UI/CopilotKit.
    Llama directamente al flujo RAG con tracing de LangSmith.
    """
    try:
        body = await request.json()
        
        # Extraer el mensaje del usuario del formato AG-UI
        messages = body.get("messages", [])
        user_message = ""
        
        # AG-UI envía mensajes en formato específico
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    user_message = content
                elif isinstance(content, list):
                    # Contenido puede ser una lista de partes
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            user_message = part.get("text", "")
                        elif isinstance(part, str):
                            user_message = part
        
        if not user_message:
            # Fallback: buscar en otras estructuras posibles
            user_message = body.get("message", body.get("query", body.get("input", "")))
        
        user_id = body.get("user_id", body.get("threadId", "usuario_web"))
        
        # Ejecutar el flujo RAG completo con tracing
        respuesta = await asistente.iniciar_flujo(user_message, user_id=user_id)
        
        # Generar respuesta en formato streaming compatible con AG-UI
        async def generate_stream():
            message_id = str(uuid.uuid4())
            
            # Evento RUN_STARTED (requerido por AG-UI)
            yield f"data: {json.dumps({'type': 'RUN_STARTED', 'runId': message_id, 'threadId': user_id})}\n\n"
            
            # Evento TEXT_MESSAGE_START
            yield f"data: {json.dumps({'type': 'TEXT_MESSAGE_START', 'messageId': message_id, 'role': 'assistant'})}\n\n"
            
            # Evento TEXT_MESSAGE_CONTENT (enviar respuesta completa)
            yield f"data: {json.dumps({'type': 'TEXT_MESSAGE_CONTENT', 'messageId': message_id, 'delta': respuesta})}\n\n"
            
            # Evento TEXT_MESSAGE_END
            yield f"data: {json.dumps({'type': 'TEXT_MESSAGE_END', 'messageId': message_id})}\n\n"
            
            # Evento RUN_FINISHED
            yield f"data: {json.dumps({'type': 'RUN_FINISHED', 'runId': message_id, 'threadId': user_id})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Respuesta de error en streaming
        async def error_stream():
            error_msg = f"Lo siento, hubo un error al procesar tu consulta: {str(e)}"
            message_id = str(uuid.uuid4())
            yield f"data: {json.dumps({'type': 'RUN_STARTED', 'runId': message_id, 'threadId': 'error'})}\n\n"
            yield f"data: {json.dumps({'type': 'TEXT_MESSAGE_START', 'messageId': message_id, 'role': 'assistant'})}\n\n"
            yield f"data: {json.dumps({'type': 'TEXT_MESSAGE_CONTENT', 'messageId': message_id, 'delta': error_msg})}\n\n"
            yield f"data: {json.dumps({'type': 'TEXT_MESSAGE_END', 'messageId': message_id})}\n\n"
            yield f"data: {json.dumps({'type': 'RUN_FINISHED', 'runId': message_id, 'threadId': 'error'})}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream"
        )

# Mantener el endpoint ADK como fallback en otra ruta (opcional)
# add_adk_fastapi_endpoint(app, adk_fisica_agent, path="/adk")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "AsistenteFisicaGEPA", "version": "2.0.0", "tracing": "langsmith"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
