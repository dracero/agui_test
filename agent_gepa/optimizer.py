"""
Optimizer for GEPA Physics Assistant - Full RAG Pipeline
Este optimizer entrena un agente profesor de física que responde consultas de forma clara y precisa,
con explicaciones pedagógicas de las expresiones matemáticas y demostraciones sencillas.
El sistema usa: clasificación → búsqueda vectorial → respuesta educativa detallada
"""

import dspy
from dspy.teleprompt import GEPA
from dspy_modules import RAGModule, Responder
import os
import json
import torch
import time
import random
import signal
import sys
import re
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from transformers import AutoTokenizer, AutoModel

load_dotenv()

# Configure DSPy with Gemini
gemini_key = os.getenv("GOOGLE_API_KEY")
lm = dspy.LM(model="gemini/gemini-2.5-flash", api_key=gemini_key)
dspy.settings.configure(lm=lm)

# --- Qdrant Search Helper ---
class QdrantSearcher:
    """Helper class to perform vector search in Qdrant - mirrors agent.py functionality"""
    
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_KEY")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "documentos_pdf")
        
        # Initialize embedding model (same as agent.py - Spanish fine-tuned)
        self.model_name = "jaimevera1107/all-MiniLM-L6-v2-similarity-es"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to("cpu")
        
        # Initialize Qdrant client (sync version for optimizer)
        self.client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        
        print("✅ QdrantSearcher initialized")
    
    def search(self, query: str, top_k: int = 5) -> str:
        """Search documents and return formatted context"""
        try:
            # Generate embedding for query
            inputs = self.tokenizer(
                [query],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            query_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy().flatten()
            
            # Search in Qdrant usando query_points (search está deprecado)
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                limit=top_k
            ).points
            
            # Load metadata
            metadata = {}
            if os.path.exists("pdf_metadata.json"):
                with open("pdf_metadata.json", "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                meta = metadata.get(str(result.id), {})
                payload = result.payload or {}
                text = meta.get("chunk", payload.get("text", "Texto no disponible"))
                pdf = meta.get("pdf", payload.get("pdf_name", "N/A"))
                formatted_results.append(f"--- Fragmento {i} (PDF: {pdf}) ---\n{text}")
            
            return "\n\n".join(formatted_results) if formatted_results else "No se encontraron documentos relevantes."
            
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            return f"Error en búsqueda: {str(e)}"
    
    def __deepcopy__(self, memo):
        """
        Custom deep copy para evitar warnings de DSPy.
        Reutiliza el modelo y cliente en lugar de copiarlos (son recursos compartibles).
        """
        import copy
        # Crear nueva instancia sin llamar __init__
        new_instance = QdrantSearcher.__new__(QdrantSearcher)
        
        # Copiar atributos simples
        new_instance.qdrant_url = self.qdrant_url
        new_instance.qdrant_api_key = self.qdrant_api_key
        new_instance.collection_name = self.collection_name
        new_instance.model_name = self.model_name
        
        # Compartir (no copiar) recursos pesados - es seguro porque son read-only
        new_instance.tokenizer = self.tokenizer
        new_instance.model = self.model
        new_instance.client = self.client
        
        memo[id(self)] = new_instance
        return new_instance


# --- Full RAG Module Wrapper ---
class FullRAGPipeline(dspy.Module):
    """
    Complete RAG pipeline that mirrors agent.py flow:
    1. Classify query using DSPy RAGModule
    2. Generate search query
    3. Search in Qdrant (real vector search)
    4. Generate clear response whit math expressions and derivations
    """
    
    def __init__(self, syllabus: str = ""):
        super().__init__()
        self.rag_module = RAGModule()
        self.searcher = QdrantSearcher()
        self.syllabus = syllabus
    
    def forward(self, user_query: str, memory_context: str = "No context"):
        # Pequeño delay para evitar rate limits
        time.sleep(1)
        
        # Step 1 & 2: Classify and generate search query (DSPy)
        prediction = self.rag_module(
            syllabus=self.syllabus,
            memory_context=memory_context,
            user_query=user_query
        )
        
        query_type = prediction.query_type
        classification = prediction.classification
        search_query = prediction.search_query
        
        # Step 3: Real vector search in Qdrant
        retrieved_context = self.searcher.search(search_query)
        
        # Step 4: Generate response as physics professor
        response = self.rag_module.generate_response(
            user_query=user_query,
            memory_context=memory_context,
            classification=classification,
            retrieved_context=retrieved_context
        )
        
        return dspy.Prediction(
            query_type=query_type,
            classification=classification,
            search_query=search_query,
            retrieved_context=retrieved_context,
            response=response
        )


# --- Metric ---
class ResponseJudge(dspy.Signature):
    """Evalúa si una respuesta es apropiada para un profesor de física - clara, precisa y pedagógica."""
    question = dspy.InputField()
    answer = dspy.InputField()
    score = dspy.OutputField(desc="Puntaje entre 0 y 10. CRITERIOS SOCRÁTICOS: ALTO (8-10): 1) Responde con una pregunta guía o pista relevante que ayuda a pensar, 2) NO da la solución directa (a menos que el usuario lo pida explícitamente), 3) Valida el input del usuario, 4) Es pedagógico y motivador. BAJO (0-3): 1) Da la respuesta directa inmediatamente sin que se lo pidan, 2) Es confuso o incorrecto, 3) Inventa información fuera de contexto.")
    reasoning = dspy.OutputField()

def validate_response(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """Métrica basada en LLM que evalúa la calidad pedagógica de las respuestas de física"""
    
    # Delay inicial para evitar rate limits
    time.sleep(2)  # 2 segundos entre cada evaluación
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            judge = dspy.ChainOfThought(ResponseJudge)
            result = judge(question=gold.user_query, answer=pred.response)
            
            # Parse score - extraer solo el número, ignorando texto adicional
            score_text = str(result.score).strip()
            
            # Usar regex para extraer el primer número (puede ser decimal)
            match = re.search(r'(\d+\.?\d*)', score_text)
            if match:
                score = float(match.group(1))
            else:
                print(f"⚠️ No se pudo parsear score: '{score_text}', usando 0.0")
                score = 0.0
            
            # Limitar score entre 0 y 10
            score = max(0.0, min(10.0, score))
            return score / 10.0
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "quota" in error_msg or "429" in error_msg:
                # Rate limit error - esperar más tiempo
                wait_time = (2 ** attempt) * 5 + random.uniform(1, 3)  # Exponential backoff
                print(f"⚠️ Rate limit alcanzado. Esperando {wait_time:.1f}s antes de reintentar... (intento {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                # Otro tipo de error
                print(f"❌ Error en validación: {e}")
                if attempt == max_retries - 1:
                    return 0.0
                time.sleep(2)
    
    return 0.0


# --- Optimization Script ---
# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_flag
    if not shutdown_flag:
        shutdown_flag = True
        print("\n\n⚠️ Interrupción detectada. Cerrando gracefully...")
        print("   Por favor espera unos segundos para guardar el progreso...")
        time.sleep(2)
    else:
        print("\n⚠️ Forzando salida...")
        sys.exit(1)

def optimize_agent():
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting Full RAG Pipeline optimization...")
    
    # Load syllabus if available
    syllabus = ""
    if os.path.exists("pdf_metadata.json"):
        print("ℹ️ Found pdf_metadata.json - Qdrant should have data")
    
    # 1. Create the full pipeline as the student module
    print("📦 Initializing Full RAG Pipeline...")
    student = FullRAGPipeline(syllabus=syllabus)
    
    # 2. Training examples - diverse mix of exercises and conceptual questions
    # The system will fetch real context from Qdrant and automatically classify query type
    # PROFESOR DE FÍSICA - Explicaciones claras, con expresiones matemáticas y demostraciones
    trainset = [
        # CASO 1: Pregunta conceptual -> Guía Socrática
        dspy.Example(
            user_query="¿Cuál es la diferencia entre una onda transversal y una longitudinal?",
            response="¡Buena pregunta! Pensemos en cómo se mueven las partículas. En una cuerda (onda transversal), ¿hacia dónde se mueve la cuerda cuando la onda avanza hacia adelante? ¿Y qué pasa con el sonido en el aire (longitudinal)?"
        ).with_inputs("user_query"),

        # CASO 2: Ejercicio práctico -> Pregunta sobre primer paso
        dspy.Example(
            user_query="Un bloque de masa m baja por un plano inclinado con rozamiento. ¿Cuáles son las fuerzas?",
            response="Analicemos el diagrama de cuerpo libre. Si el bloque tiene masa, seguro hay una fuerza vertical hacia abajo, ¿verdad? ¿Cómo se llama esa fuerza? Y si hay contacto con la superficie, ¿qué fuerza impide que el bloque se hunda en el plano?"
        ).with_inputs("user_query"),

        # CASO 3: Usuario pide la respuesta explícitamente -> Respuesta Directa
        dspy.Example(
            user_query="No entiendo nada, dame la solución del problema del plano inclinado por favor.",
            response="Entiendo, veamos la solución completa. Las fuerzas son: 1) **Peso (mg)** hacia abajo, 2) **Normal (N)** perpendicular al plano, y 3) **Fricción (fr)** opuesta al movimiento. La ecuación en el eje del movimiento es: mg·sen(θ) - fr = ma."
        ).with_inputs("user_query"),

        # CASO 4: Concepto erróneo -> Corrección guiada
        dspy.Example(
            user_query="La energía cinética se conserva en todos los choques, ¿verdad?",
            response="Cuidado con eso. En los choques elásticos sí se conserva, pero ¿qué pasa en un choque inelástico, como cuando dos bolas de plastilina se pegan? ¿A dónde crees que va esa energía de movimiento?"
        ).with_inputs("user_query"),

        # CASO 5: Pregunta sobre fórmula -> Pista sobre variables
        dspy.Example(
            user_query="¿Cómo calculo el momento de inercia de un disco?",
            response="Depende del eje de rotación. Si gira por su centro, la fórmula involucra la masa M y el radio R. ¿Recuerdas si el factor era 1/2 o MR² completo? Piensa en cómo está distribuida la masa respecto al centro."
        ).with_inputs("user_query"),


    ]
    
    # 3. Set up GEPA optimizer
    print("⚙️ Setting up GEPA optimizer...")
    print("   Configurado con delays para evitar rate limits de Gemini")
    print("   Usando num_threads=1 para evitar problemas de concurrencia")
    reflection_lm = dspy.LM(model="gemini/gemini-2.5-flash", api_key=gemini_key, temperature=0.7)
    teleprompter = GEPA(
        metric=validate_response, 
        max_metric_calls=25,  # Reducido de 50 a 25
        reflection_lm=reflection_lm,
        num_threads=1  # Evitar problemas de concurrencia
    )
    
    # 4. Compile/Optimize
    print("🔧 Compiling/Optimizing with GEPA (full RAG pipeline)...")
    print("   This will use real Qdrant searches during optimization!")
    
    try:
        optimized_pipeline = teleprompter.compile(student, trainset=trainset)
        
        # 5. Save optimized responder weights
        # Note: We save the responder specifically since that's what agent.py loads
        optimized_pipeline.rag_module.responder.save("optimized_responder.json")
        print("✅ Optimization complete! Saved to optimized_responder.json")
        print("   El agente ahora responderá como un profesor de física con explicaciones claras y precisas.")
    except KeyboardInterrupt:
        print("\n\n⚠️ Optimización interrumpida por el usuario")
        print("   No se guardaron cambios")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error durante la optimización: {e}")
        print("   Verifica los logs arriba para más detalles")
        sys.exit(1)


if __name__ == "__main__":
    optimize_agent()
