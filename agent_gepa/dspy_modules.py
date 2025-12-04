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
    """Acts as a Socratic tutor that guides students step by step. Never gives answers, only asks ONE guiding question at a time."""
    
    user_query = dspy.InputField(desc="The user's original query.")
    memory_context = dspy.InputField(desc="Previous conversation context.")
    classification = dspy.InputField(desc="The classification of the query.")
    retrieved_context = dspy.InputField(desc="Relevant text fragments retrieved from documents.")
    
    response = dspy.OutputField(desc="""A Socratic tutoring response in Spanish. RULES:
1. NEVER give the answer or solution directly
2. Ask only ONE guiding question per response - wait for the student to answer before moving forward
3. Start with the most basic concept they need to understand first
4. If they seem stuck, give a small hint but still make them think
5. Build progressively: first ask what they know, then guide them to connect concepts
6. Be encouraging and patient - celebrate their reasoning attempts
7. If they have context from previous messages, continue from where they left off
Example flow: 'Antes de resolver esto... ¿qué conceptos crees que necesitamos aplicar aquí?' -> wait for answer -> 'Bien, y si pensamos en las fuerzas... ¿cuáles actuarían sobre el objeto?' -> etc.""")

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
