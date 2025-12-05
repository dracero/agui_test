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
        
        # Initialize embedding model (same as agent.py)
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
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
    score = dspy.OutputField(desc="Puntaje entre 0 y 10. Criterios para ALTO puntaje (8-10): 1) Explica conceptos de forma clara y precisa, 2) Incluye las expresiones matemáticas relevantes con explicación de sus variables y significado, 3) Proporciona demostraciones o derivaciones sencillas cuando corresponda, 4) Usa lenguaje pedagógico apropiado al nivel de la consulta, 5) Es completo pero conciso. Criterios para BAJO puntaje (0-3): 1) Respuesta vaga o imprecisa, 2) Falta explicación de las ecuaciones matemáticas, 3) Lenguaje confuso o demasiado técnico sin contexto, 4) No responde directamente la consulta.")
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
    
    # 2. Training examples - only user_query and expected response
    # The system will fetch real context from Qdrant
    # PROFESOR DE FÍSICA - Explicaciones claras, con expresiones matemáticas y demostraciones
    trainset = [
        dspy.Example(
            user_query="Un bloque de masa m baja por un plano inclinado con rozamiento. ¿Cuáles son las fuerzas que actúan y cómo planteo la segunda ley de Newton?",
            response="¡Excelente pregunta! En este sistema actúan tres fuerzas sobre el bloque:\n\n1. **Peso (W)**: Apunta verticalmente hacia abajo con magnitud W = mg, donde g es la aceleración de gravedad.\n2. **Normal (N)**: Perpendicular al plano inclinado.\n3. **Fuerza de rozamiento (fr)**: Paralela al plano, oponiéndose al movimiento.\n\nPara aplicar la segunda ley de Newton (F = ma), es conveniente usar un sistema de coordenadas rotado con el eje x paralelo al plano:\n\n**Descomposición del peso:**\n- Componente paralela: Wx = mg·sen(θ)\n- Componente perpendicular: Wy = mg·cos(θ)\n\n**Ecuaciones de movimiento:**\n- Eje x: mg·sen(θ) - fr = ma\n- Eje y: N - mg·cos(θ) = 0\n\nDonde fr = μN (μ es el coeficiente de fricción). De la segunda ecuación: N = mg·cos(θ), sustituyendo:\n\n**ma = mg·sen(θ) - μmg·cos(θ)**\n\nSimplificando: **a = g(sen(θ) - μcos(θ))**"
        ).with_inputs("user_query"),
        dspy.Example(
            user_query="¿Cuál es la diferencia entre una onda transversal y una longitudinal?",
            response="La diferencia fundamental está en la **dirección de oscilación** de las partículas del medio respecto a la dirección de propagación de la onda:\n\n**Onda Transversal:**\n- Las partículas oscilan perpendicular (⊥) a la dirección de propagación\n- Ejemplo: ondas en una cuerda, luz, ondas en agua\n- Tiene crestas y valles claramente definidos\n- Representación matemática: y(x,t) = A·sen(kx - ωt), donde y es el desplazamiento perpendicular\n\n**Onda Longitudinal:**\n- Las partículas oscilan paralela (∥) a la dirección de propagación\n- Ejemplo: sonido, ondas sísmicas P\n- Tiene compresiones y rarefacciones\n- Las partículas se comprimen y expanden en la misma dirección del movimiento de la onda\n\n**Parámetros comunes:**\nAmbas tienen: velocidad v = λf (donde λ es longitud de onda y f frecuencia), amplitud A, y pueden expresarse con la ecuación de onda general."
        ).with_inputs("user_query"),
        dspy.Example(
            user_query="Explica la ley de Snell y qué sucede cuando la luz pasa de un medio con mayor índice de refracción a uno menor.",
            response="La **Ley de Snell** describe cómo cambia la dirección de un rayo de luz al pasar entre dos medios con diferentes índices de refracción:\n\n**n₁·sen(θ₁) = n₂·sen(θ₂)**\n\nDonde:\n- n₁, n₂: índices de refracción de los medios 1 y 2\n- θ₁, θ₂: ángulos de incidencia y refracción (medidos desde la normal)\n\nEl índice de refracción n = c/v, donde c es la velocidad de la luz en el vacío y v en el medio.\n\n**Caso específico n₁ > n₂ (por ejemplo, agua → aire):**\n\nDe la ley de Snell: sen(θ₂) = (n₁/n₂)·sen(θ₁)\n\nComo n₁ > n₂, entonces (n₁/n₂) > 1, por lo que θ₂ > θ₁.\n\n**Resultado:** El rayo se **aleja de la normal**.\n\n**Ángulo crítico:** Existe un θc = arcsen(n₂/n₁) tal que si θ₁ > θc, ocurre **reflexión total interna** (el rayo no se transmite, solo se refleja). Este fenómeno es la base de las fibras ópticas."
        ).with_inputs("user_query"),
        dspy.Example(
            user_query="¿Cómo se calcula el centro de masa de un sistema de partículas?",
            response="El **centro de masa** es el punto donde se puede considerar concentrada toda la masa del sistema. Su posición se calcula como el promedio ponderado de las posiciones de todas las partículas:\n\n**Para un sistema de N partículas:**\n\n**R_cm = (Σ mᵢ·rᵢ) / M_total**\n\nDonde:\n- rᵢ: vector posición de la partícula i\n- mᵢ: masa de la partícula i\n- M_total = Σ mᵢ: masa total del sistema\n\n**En componentes cartesianas:**\n- x_cm = (m₁x₁ + m₂x₂ + ... + mₙxₙ) / M_total\n- y_cm = (m₁y₁ + m₂y₂ + ... + mₙyₙ) / M_total\n- z_cm = (m₁z₁ + m₂z₂ + ... + mₙzₙ) / M_total\n\n**Ejemplo práctico:** Dos masas m₁=2kg en x=0 y m₂=3kg en x=5m:\nx_cm = (2·0 + 3·5)/(2+3) = 15/5 = 3m\n\nEl centro de masa está más cerca de la masa mayor, como esperábamos intuitivamente."
        ).with_inputs("user_query"),
        dspy.Example(
            user_query="Define el momento de inercia.",
            response="El **momento de inercia (I)** es la medida de la resistencia de un cuerpo a cambiar su velocidad angular. Es el análogo rotacional de la masa en el movimiento lineal.\n\n**Definición matemática:**\n\n**I = Σ mᵢ·rᵢ²** (para partículas discretas)\n**I = ∫ r²·dm** (para cuerpos continuos)\n\nDonde:\n- mᵢ: masa del elemento i\n- rᵢ: distancia perpendicular del elemento al eje de rotación\n- dm: elemento infinitesimal de masa\n\n**Analogía con movimiento lineal:**\n- Lineal: F = ma → Energía cinética = ½mv²\n- Rotacional: τ = Iα → Energía cinética = ½Iω²\n\n**Ejemplos de momentos de inercia:**\n- Cilindro sólido (eje central): I = ½MR²\n- Esfera sólida (eje por centro): I = ⅖MR²\n- Varilla delgada (eje por extremo): I = ⅓ML²\n\n**Propiedad clave:** El momento de inercia depende NO SOLO de la masa, sino también de cómo está distribuida respecto al eje de rotación. Por eso objetos de igual masa pueden tener diferentes momentos de inercia."
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
