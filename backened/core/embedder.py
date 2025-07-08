# from sentence_transformers import SentenceTransformer
#
# # Load the model once
# #model = SentenceTransformer("all-MiniLM-L6-v2")
# model = SentenceTransformer("BAAI/bge-large-en-v1.5")
# def get_embedding(text: str):
#     return model.encode(text, convert_to_tensor=False).tolist()


# core/embedder.py

from sentence_transformers import SentenceTransformer

# Load the E5 Large v2 model (Hugging Face ID: intfloat/e5-large-v2)
model = SentenceTransformer("intfloat/e5-large-v2")

def get_embedding(text: str):
    # E5 models work best when you prefix with "passage: "
    prompt = "passage: " + text.strip().replace("\n", " ")
    return model.encode(prompt, convert_to_tensor=False).tolist()
