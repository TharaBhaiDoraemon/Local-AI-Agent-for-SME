from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import shutil

embeddings = OllamaEmbeddings(model="bge-m3")
db_location = "./chrome_langchain_db"

# Initialize vector store (don't delete existing DB)
vector_store = Chroma(
    collection_name="restaurant_reviews",
    persist_directory=db_location,
    embedding_function=embeddings
)

def get_processed_files():
    """Get the list of already processed files from the vector store"""
    processed_files = set()
    if os.path.exists(db_location) and vector_store._collection.count() > 0:
        try:
            existing_docs = vector_store.get()
            if "metadatas" in existing_docs:
                for metadata in existing_docs["metadatas"]:
                    if "source" in metadata:
                        processed_files.add(metadata["source"])
        except Exception as e:
            print(f"Error getting processed files: {e}")
    return processed_files

def process_documents():
    """Process all documents in the attachments directory"""
    processed_files = get_processed_files()
    attachments_dir = "attachments"

    if not os.path.exists(attachments_dir):
        os.makedirs(attachments_dir)
        print(f"Created {attachments_dir} directory")
        return

    all_documents = []
    for filename in os.listdir(attachments_dir):
        file_path = os.path.join(attachments_dir, filename)

        # Skip if already processed
        if file_path in processed_files:
            print(f"Skipping already processed file: {filename}")
            continue

        print(f"Processing file: {filename}")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents = loader.load_and_split()
                print(f"Loaded {len(documents)} documents from {filename}")
            elif filename.endswith(".csv"):
                loader = CSVLoader(file_path)
                documents = loader.load()
                documents = text_splitter.split_documents(documents)
                print(f"Loaded {len(documents)} documents from {filename}")
            elif filename.endswith(".docx"):
                loader = UnstructuredWordDocumentLoader(file_path)
                documents = loader.load()
                documents = text_splitter.split_documents(documents)
                print(f"Loaded {len(documents)} documents from {filename}")
            else:
                print(f"Skipping file: {filename}")
                continue
            all_documents.extend(documents)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    if all_documents:
        vector_store.add_documents(documents=all_documents)
        print(f"Added {len(all_documents)} document chunks to vector store")

def get_vector_store():
    """Get the vector store instance"""
    return vector_store

# Process documents on initial import
process_documents()

# Create retriever
retriever = vector_store.as_retriever(
    search_kwargs={"k": 5}
)
