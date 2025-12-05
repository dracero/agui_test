import dspy
from typing import List

# --- Signatures ---

class Classifier(dspy.Signature):
    """Classifies a physics query into a topic, subtopics, and keywords based on a syllabus."""
    
    syllabus = dspy.InputField(desc="The physics syllabus containing topics.")
    memory_context = dspy.InputField(desc="Previous conversation context.")
    user_query = dspy.InputField(desc="The user's query to be classified.")
    
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
    
    response = dspy.OutputField(desc="""Una respuesta educativa en español como profesor de física. REGLAS:
1. Explica los conceptos de forma CLARA y DIRECTA - responde la pregunta
2. Incluye las EXPRESIONES MATEMÁTICAS relevantes y explica cada variable
3. Proporciona DEMOSTRACIONES o DERIVACIONES sencillas paso a paso cuando corresponda
4. Usa un lenguaje pedagógico apropiado al nivel de la consulta
5. Estructura la respuesta de forma organizada (usa negritas ** para destacar términos clave)
6. Cuando sea útil, incluye:
   - Definiciones claras de conceptos
   - Ecuaciones con explicación de cada término
   - Pasos de derivación matemática
   - Ejemplos numéricos simples si ayudan a entender
7. Sé completo pero conciso - no des información innecesaria
8. Si hay contexto previo de la conversación, considera lo que ya se discutió
Ejemplo: Para una pregunta sobre fuerzas, explica qué fuerzas actúan, escribe F = ma indicando qué es cada símbolo, y muestra cómo aplicarlo paso a paso.""")

# --- Modules ---

class RAGModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classifier = dspy.ChainOfThought(Classifier)
        self.search_generator = dspy.ChainOfThought(SearchQueryGenerator)
        self.responder = dspy.ChainOfThought(Responder)
    
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
            classification=classification_result.classification,
            search_query=search_result.search_query
        )

    def generate_response(self, user_query, memory_context, classification, retrieved_context):
        # Step 3: Generate Response (called after search)
        response_result = self.responder(
            user_query=user_query,
            memory_context=memory_context,
            classification=classification,
            retrieved_context=retrieved_context
        )
        return response_result.response
