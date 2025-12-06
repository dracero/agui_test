import dspy
from typing import List

# --- Signatures ---

class Classifier(dspy.Signature):
    """Classifies a physics query into a topic, subtopics, keywords, and query type (exercise vs conceptual)."""
    
    syllabus = dspy.InputField(desc="The physics syllabus containing topics.")
    memory_context = dspy.InputField(desc="Previous conversation context.")
    user_query = dspy.InputField(desc="The user's query to be classified.")
    
    query_type = dspy.OutputField(desc="Type of query: 'EJERCICIO' if it's a practical exercise/problem to solve, or 'CONCEPTUAL' if it's asking for explanation of concepts, definitions, or theoretical understanding.")
    classification = dspy.OutputField(desc="The classification result including Topic, Subtopics, and Keywords.")

class SearchQueryGenerator(dspy.Signature):
    """Generates an optimized search query for a vector database based on classification and user query."""
    
    classification = dspy.InputField(desc="The classification of the user query.")
    original_query = dspy.InputField(desc="The original user query.")
    memory_context = dspy.InputField(desc="Previous conversation context.")
    
    search_query = dspy.OutputField(desc="The optimized search query.")

class Responder(dspy.Signature):
    """Actúa como un profesor de física que explica conceptos de forma clara y precisa, con expresiones matemáticas y demostraciones."""
    
    user_query = dspy.InputField(desc="The user's original query.")
    memory_context = dspy.InputField(desc="Previous conversation context.")
    classification = dspy.InputField(desc="The classification of the query.")
    retrieved_context = dspy.InputField(desc="Relevant text fragments retrieved from documents.")
    
    response = dspy.OutputField(desc="""Una respuesta educativa en español como profesor de física. REGLAS ESTRICTAS:
1. BASATE ÚNICAMENTE en el 'retrieved_context'. Si la información no está ahí, DI "No encuentro información sobre esto en los documentos disponibles".
2. NO uses conocimiento externo que no esté respaldado por el contexto recuperado.
3. Explica los conceptos de forma CLARA y DIRECTA usando solo la información provista.
4. Incluye las EXPRESIONES MATEMÁTICAS que aparezcan en el contexto y explica cada variable según el texto.
5. Proporciona DEMOSTRACIONES o DERIVACIONES sencillas paso a paso SOLO si están en el contexto.
6. Usa un lenguaje pedagógico apropiado.
7. Estructura la respuesta de forma organizada (usa negritas ** para destacar términos clave).
8. Cita implícitamente la fuente mencionando "según los documentos" o "como indica el texto".
Ejemplo: "Según el texto proporcionado, la fuerza se define como..." """)

# --- Modules ---

try:
    from langsmith import traceable
except ImportError:
    # Dummy decorator if langsmith is not available
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

class RAGModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classifier = dspy.ChainOfThought(Classifier)
        self.search_generator = dspy.ChainOfThought(SearchQueryGenerator)
        self.responder = dspy.ChainOfThought(Responder)
    
    @traceable(run_type="chain", name="RAGModule_Forward_ClassifySearch")
    def forward(self, syllabus, memory_context, user_query):
        # Step 1: Classify
        classification_result = self.classifier(
            syllabus=syllabus,
            memory_context=memory_context,
            user_query=user_query
        )
        
        # Step 2: Generate Search Query
        search_result = self.search_generator(
            classification=classification_result.classification,
            original_query=user_query,
            memory_context=memory_context
        )
        
        # Note: The actual search happens outside this module in the agent logic 
        # because it involves async DB calls which DSPy modules don't handle natively 
        # in the forward pass usually (though they can). 
        # For optimization purposes, we return the intermediate outputs too.
        
        return dspy.Prediction(
            query_type=classification_result.query_type,
            classification=classification_result.classification,
            search_query=search_result.search_query
        )

    @traceable(run_type="chain", name="RAGModule_GenerateResponse")
    def generate_response(self, user_query, memory_context, classification, retrieved_context):
        # Step 3: Generate Response (called after search)
        response_result = self.responder(
            user_query=user_query,
            memory_context=memory_context,
            classification=classification,
            retrieved_context=retrieved_context
        )
        return response_result.response
