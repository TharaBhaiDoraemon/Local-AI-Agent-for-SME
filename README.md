# Local AI Agent for SME

A local AI agent that uses a Retrieval-Augmented Generation (RAG) pipeline to answer questions about a Small to Medium-sized Enterprise's (SME) documents.

## How it Works

This project uses a RAG pipeline to answer questions based on a collection of documents. The pipeline consists of the following components:

1.  **Document Loading:** The agent loads documents from the `attachments` directory. It supports PDF, CSV, and Word documents.
2.  **Vector Store:** The loaded documents are then split into smaller chunks and stored in a Chroma vector store. The embeddings are generated using the `bge-m3` model from Ollama.
3.  **Retrieval:** When a user asks a question, the agent retrieves the most relevant document chunks from the vector store.
4.  **Generation:** The retrieved document chunks and the user's question are then passed to a Large Language Model (LLM) from Ollama (phi3) to generate a final answer.

## How to Use

1.  **Install Dependencies:**
    ```
    pip install -r requirements.txt
    ```
2.  **Add Documents:** Place your PDF, CSV, or Word documents in the `attachments` directory.
3.  **Run the Agent:**
    ```
    python main.py
    ```
