# Local AI Agent for SME

A local AI agent that uses a Retrieval-Augmented Generation (RAG) pipeline to answer questions about a Small to Medium-sized Enterprise's (SME) documents.

## How it Works

This project uses a RAG pipeline to answer questions based on a collection of documents. The pipeline consists of the following components:

1.  **Document Loading:** The agent loads documents from the `attachments` directory. It supports PDF, CSV, and Word documents.
2.  **Vector Store:** The loaded documents are then split into smaller chunks and stored in a Chroma vector store. The embeddings are generated using the `bge-m3` model from Ollama.
3.  **Retrieval:** When a user asks a question, the agent retrieves the most relevant document chunks from the vector store.
4.  **Generation:** The retrieved document chunks and the user's question are then passed to a Large Language Model (LLM) from Ollama (phi3) to generate a final answer.

## How to Use

### Prerequisites

- Python 3.8 or higher
- Ollama installed and running locally
- Required Ollama models: `bge-m3` (for embeddings) and `phi3` (for LLM)

### Installation

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Ensure Ollama is Running:**
    Make sure Ollama is installed and running on your system with the required models:
    ```bash
    ollama pull bge-m3
    ollama pull phi3
    ```

### Running the Application

You can run the application in two ways:

#### Option 1: Web Interface (Recommended)

1.  **Start the Web Server:**
    ```bash
    python app.py
    ```

2.  **Access the Web Interface:**
    Open your browser and navigate to: `http://localhost:8000`

3.  **Use the Application:**
    - Upload documents using the "Upload Document" button in the sidebar
    - Ask questions in the chat interface
    - View and manage your uploaded documents
    - Get AI-powered answers based on your document content

#### Option 2: Command Line Interface

1.  **Add Documents:** Place your PDF, CSV, or Word documents in the `attachments` directory.

2.  **Run the CLI Agent:**
    ```bash
    python main.py
    ```

3.  **Ask Questions:** Type your questions and press Enter. Type 'q' to quit.

## Features

### 🆕 3-Level Access Control System
- **Level 1**: Single document access (basic users)
- **Level 2**: Multiple documents access (team members)
- **Level 3**: Full access to all documents (managers)
- **IT Admin Portal**: Separate portal for managing user access levels
- **Document Filtering**: Users only see and query accessible documents
- **Access Level Badges**: Visual indicators of user permissions

See [QUICK_START.md](QUICK_START.md) for setup guide and [ACCESS_CONTROL_GUIDE.md](ACCESS_CONTROL_GUIDE.md) for detailed documentation.

### Web Interface
- Modern, responsive web UI
- Real-time document upload and management
- Chat-based Q&A interface
- Document source tracking
- Status monitoring
- Multi-user profile management with PIN protection
- Access control integration

### Supported Document Types
- PDF (.pdf)
- CSV (.csv)
- Microsoft Word (.docx)

### API Endpoints

The web server exposes the following REST API endpoints:

#### Document Operations
- `POST /api/ask` - Ask a question about your documents
- `POST /api/upload` - Upload a new document
- `GET /api/documents` - List all uploaded documents (filtered by access level)
- `DELETE /api/documents/{filename}` - Delete a document
- `GET /api/status` - Get application status

#### Access Control (Admin)
- `POST /api/admin/login` - Admin authentication
- `POST /api/admin/users/{user_id}/access-level` - Assign user access level
- `POST /api/admin/users/{user_id}/assign-documents` - Assign specific documents
- `GET /api/admin/documents` - List all documents with access levels
- `PUT /api/admin/documents/{doc_id}/access-level` - Update document access level
- `GET /api/admin/statistics` - Get system statistics

#### Access Control (User)
- `GET /api/users/{user_id}/accessible-documents` - Get user's accessible documents
- `GET /api/users/{user_id}/access-info` - Get user's access level info

For complete API documentation, see [ACCESS_CONTROL_GUIDE.md](ACCESS_CONTROL_GUIDE.md).
