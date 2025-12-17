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
    
    response = dspy.OutputField(desc="""Respuesta educativa usando el MÉTODO SOCRÁTICO.
REGLAS ESTRICTAS:
1. SI EL USUARIO HACE UNA PREGUNTA DE CONCEPTO O EJERCICIO: NO des la respuesta completa directa. En su lugar, haz una pregunta guía o da una pista que ayude al alumno a razonar el siguiente paso.
2. SI EL USUARIO PIDE EXPLÍCITAMENTE LA SOLUCIÓN (ej: "dame la respuesta", "resuelvelo"): ENTONCES SÍ da la explicación completa y detallada.
3. BASATE ÚNICAMENTE en el 'retrieved_context'. Si no hay info, dilo.
4. Sé amable y motivador. Valida si el alumno intentó algo.
5. Usa negritas ** para destacar términos.

Ejemplo Socrático:
Usuario: "¿Cómo calculo la fuerza?"
Asistente: "¿Recuerdas la segunda ley de Newton? ¿Qué relación establece entre masa y aceleración?" 

Ejemplo Directo (Solo si se pide):
Usuario: "Resuelve esto por favor"
Asistente: "Claro, aquí tienes la resolución paso a paso..." """)

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
