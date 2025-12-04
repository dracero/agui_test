"""
Optimizer for GEPA Physics Assistant - Full RAG Pipeline
This optimizer uses the complete RAG system: classification → vector search → Socratic response
"""

import dspy
from dspy.teleprompt import GEPA
from dspy_modules import RAGModule, Responder
import os
import json
import torch
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
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k
            )
            
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


# --- Full RAG Module Wrapper ---
class FullRAGPipeline(dspy.Module):
    """
    Complete RAG pipeline that mirrors agent.py flow:
    1. Classify query using DSPy RAGModule
    2. Generate search query
    3. Search in Qdrant (real vector search)
    4. Generate Socratic response
    """
    
    def __init__(self, syllabus: str = ""):
        super().__init__()
        self.rag_module = RAGModule()
        self.searcher = QdrantSearcher()
        self.syllabus = syllabus
    
    def forward(self, user_query: str, memory_context: str = "No context"):
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
        
        # Step 4: Generate Socratic response
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
    """Evaluates whether a response is truly Socratic - guiding without giving answers."""
    question = dspy.InputField()
    answer = dspy.InputField()
    score = dspy.OutputField(desc="A score between 0 and 10. CRITICAL: Give LOW scores (0-3) if the response gives the answer directly. Give HIGH scores (8-10) only if: 1) It asks guiding questions, 2) It provides hints without revealing the solution, 3) It encourages the student to think and discover, 4) It NEVER states the answer explicitly.")
    reasoning = dspy.OutputField()

def validate_response(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """LLM-based metric that penalizes direct answers"""
    judge = dspy.ChainOfThought(ResponseJudge)
    result = judge(question=gold.user_query, answer=pred.response)
    try:
        score = float(result.score)
        return score / 10.0
    except:
        return 0.0


# --- Optimization Script ---
def optimize_agent():
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
    # SOCRATIC EXAMPLES - ONE guiding question at a time, step by step
    trainset = [
        dspy.Example(
            user_query="Un bloque de masa m baja por un plano inclinado con rozamiento. ¿Cuáles son las fuerzas que actúan y cómo planteo la segunda ley de Newton?",
            response="¡Buena pregunta! 🤔 Antes de identificar todas las fuerzas, empecemos por lo básico: cuando un objeto está cerca de la Tierra, ¿qué fuerza siempre actúa sobre él, sin importar nada más?"
        ).with_inputs("user_query"),
        dspy.Example(
            user_query="¿Cuál es la diferencia entre una onda transversal y una longitudinal?",
            response="¡Excelente tema! 🌊 Para entender esto, primero pensemos en algo: cuando una onda viaja por un medio, ¿qué es lo que se 'perturba' o 'mueve'? ¿Son las partículas del medio, o es algo más?"
        ).with_inputs("user_query"),
        dspy.Example(
            user_query="Explica la ley de Snell y qué sucede cuando la luz pasa de un medio con mayor índice de refracción a uno menor.",
            response="¡Interesante! 🔦 Empecemos por lo fundamental: ¿qué representa físicamente el 'índice de refracción' de un medio? ¿Por qué creés que algunos materiales tienen un índice mayor que otros?"
        ).with_inputs("user_query"),
        dspy.Example(
            user_query="¿Cómo se calcula el centro de masa de un sistema de partículas?",
            response="¡Muy buena pregunta! ⚖️ Antes de ver la fórmula, pensemos en la intuición: si tenés dos masas, una muy pesada y una liviana, ¿dónde esperarías que esté el 'punto de equilibrio' del sistema? ¿Más cerca de cuál?"
        ).with_inputs("user_query"),
        dspy.Example(
            user_query="Define el momento de inercia.",
            response="¡Excelente tema! 🔄 Para entender el momento de inercia, primero recordemos: en movimiento lineal, ¿qué propiedad de un objeto determina qué tan difícil es cambiar su velocidad? ¿Cómo se llama esa propiedad?"
        ).with_inputs("user_query"),
    ]
    
    # 3. Set up GEPA optimizer
    print("⚙️ Setting up GEPA optimizer...")
    reflection_lm = dspy.LM(model="gemini/gemini-2.5-flash", api_key=gemini_key, temperature=0.7)
    teleprompter = GEPA(metric=validate_response, max_metric_calls=50, reflection_lm=reflection_lm)
    
    # 4. Compile/Optimize
    print("🔧 Compiling/Optimizing with GEPA (full RAG pipeline)...")
    print("   This will use real Qdrant searches during optimization!")
    optimized_pipeline = teleprompter.compile(student, trainset=trainset)
    
    # 5. Save optimized responder weights
    # Note: We save the responder specifically since that's what agent.py loads
    optimized_pipeline.rag_module.responder.save("optimized_responder.json")
    print("✅ Optimization complete! Saved to optimized_responder.json")
    print("   The agent will now use Socratic responses with real RAG context.")

if __name__ == "__main__":
    optimize_agent()
