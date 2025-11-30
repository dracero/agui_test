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
    """Generates a helpful and educational response to a physics question based on retrieved documents."""
    
    user_query = dspy.InputField(desc="The user's original query.")
    memory_context = dspy.InputField(desc="Previous conversation context.")
    classification = dspy.InputField(desc="The classification of the query.")
    retrieved_context = dspy.InputField(desc="Relevant text fragments retrieved from documents.")
    
    response = dspy.OutputField(desc="The final educational response.")

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
