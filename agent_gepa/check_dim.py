from langchain_huggingface import HuggingFaceEmbeddings

model_name = "jaimevera1107/all-MiniLM-L6-v2-similarity-es"
embeddings = HuggingFaceEmbeddings(model_name=model_name)
vector = embeddings.embed_query("test")
print(f"Dimension: {len(vector)}")
