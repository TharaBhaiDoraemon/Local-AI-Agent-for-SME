from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

embeddings = OllamaEmbeddings(model="bge-m3")
db_location = "./chrome_langchain_db"
vector_store = Chroma(
    collection_name="restaurant_reviews",
    persist_directory=db_location,
    embedding_function=embeddings
)

# Get the list of already processed files from the vector store
processed_files = set()
if os.path.exists(db_location) and vector_store._collection.count() > 0:
    existing_docs = vector_store.get()
    if "metadatas" in existing_docs:
        for metadata in existing_docs["metadatas"]:
            if "source" in metadata:
                processed_files.add(metadata["source"])

attachments_dir = "attachments"
all_documents = []
for filename in os.listdir(attachments_dir):
    file_path = os.path.join(attachments_dir, filename)
    if file_path in processed_files:
        continue

    if filename.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        documents = loader.load_and_split()
    elif filename.endswith(".csv"):
        loader = CSVLoader(file_path)
        documents = loader.load()
    elif filename.endswith(".docx"):
        loader = UnstructuredWordDocumentLoader(file_path)
        documents = loader.load_and_split()
    else:
        continue
    all_documents.extend(documents)

if all_documents:
    vector_store.add_documents(documents=all_documents)


retriever = vector_store.as_retriever(
    search_kwargs={"k": 5}
)
