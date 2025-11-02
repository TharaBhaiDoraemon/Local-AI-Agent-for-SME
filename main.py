from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever
import json
from pathlib import Path

# Load model configuration
MODEL_CONFIG_FILE = Path("./model_config.json")

def load_model_config():
    """Load model configuration from disk"""
    if not MODEL_CONFIG_FILE.exists():
        return {"llm_model": "phi3:latest", "embedding_model": "bge-m3:latest"}
    try:
        with open(MODEL_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading model config: {e}")
        return {"llm_model": "phi3:latest", "embedding_model": "bge-m3:latest"}

# Get LLM model from config
model_config = load_model_config()
model = OllamaLLM(model=model_config["llm_model"])

template = """
You are an expert in answering questions.

Here are some of information you can fetch: {reviews}

Here is the question to answer: {question}

Suggest 2 new questions
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("\n\n-------------------------------")
    question = input("Ask your question (q to quit): ")
    print("\n\n")
    if question == "q":
        break
    
    reviews = retriever.invoke(question)
    result = chain.invoke({"reviews": reviews, "question": question})
    print(result)
