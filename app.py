from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
from pathlib import Path
import uvicorn
import json
from datetime import datetime
import uuid

# Import the retriever and setup from vector.py
from vector import retriever, get_vector_store, process_documents
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# Import access control system
from access_control import (
    access_control,
    ACCESS_LEVEL_1,
    ACCESS_LEVEL_2,
    ACCESS_LEVEL_3,
    ACCESS_LEVEL_ADMIN,
    DocumentAccess,
    UserAccessProfile,
    ITAdmin
)

app = FastAPI(title="Local AI Agent for SME")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup LLM and chain
model = OllamaLLM(model="phi3")

template = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know. Be concise and provide informative answers.

Here is the information you can use: {context}

Here is the question to answer: {input}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Pydantic models
class QuestionRequest(BaseModel):
    question: str
    profile_id: str
    chat_id: Optional[str] = None

class QuestionResponse(BaseModel):
    answer: str
    sources: List[str]

class StatusResponse(BaseModel):
    status: str
    documents_count: int
    vector_db_status: str

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    sources: Optional[List[str]] = []
    timestamp: str

class ChatSession(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessage]
    group_id: Optional[str] = None

class Group(BaseModel):
    id: str
    name: str
    created_at: str
    order: int  # For custom ordering

class CreateChatRequest(BaseModel):
    title: Optional[str] = "New Chat"
    group_id: Optional[str] = None

class CreateGroupRequest(BaseModel):
    name: str

class UpdateGroupRequest(BaseModel):
    name: str

class MoveChatRequest(BaseModel):
    group_id: Optional[str] = None

class Profile(BaseModel):
    id: str
    name: str
    pin: Optional[str] = None  # Optional PIN/password
    hint: Optional[str] = None  # Optional hint for PIN
    is_guest: bool = False
    created_at: str
    has_pin: bool = False  # Indicates if profile is PIN-protected (safe to send to frontend)
    profile_picture: Optional[str] = None  # Path to profile picture

class CreateProfileRequest(BaseModel):
    name: str
    pin: Optional[str] = None
    hint: Optional[str] = None

class LoginProfileRequest(BaseModel):
    profile_id: str
    pin: Optional[str] = None

# Access Control Models
class AssignAccessLevelRequest(BaseModel):
    user_id: str
    access_level: int

class AssignDocumentsRequest(BaseModel):
    user_id: str
    document_ids: List[str]

class ITAdminLoginRequest(BaseModel):
    username: str
    password: str

class CreateITAdminRequest(BaseModel):
    username: str
    password: str

class UpdateDocumentAccessRequest(BaseModel):
    document_id: str
    access_level: int

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    pin: Optional[str] = None
    hint: Optional[str] = None

# Ensure directories exist
ATTACHMENTS_DIR = Path("./attachments")
STATIC_DIR = Path("./static")
CHAT_HISTORY_DIR = Path("./chat_history")
PROFILES_FILE = Path("./profiles.json")
PROFILE_PICTURES_DIR = Path("./profile_pictures")
ATTACHMENTS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
CHAT_HISTORY_DIR.mkdir(exist_ok=True)
PROFILE_PICTURES_DIR.mkdir(exist_ok=True)

# Profile Management Functions
def load_profiles() -> List[Profile]:
    """Load all profiles from disk"""
    if not PROFILES_FILE.exists():
        # Create default guest profile
        guest_profile = Profile(
            id="guest",
            name="Guest",
            is_guest=True,
            created_at=datetime.now().isoformat()
        )
        save_profiles([guest_profile])
        return [guest_profile]

    try:
        with open(PROFILES_FILE, 'r') as f:
            data = json.load(f)
            return [Profile(**profile) for profile in data]
    except Exception as e:
        print(f"Error loading profiles: {e}")
        return []

def save_profiles(profiles: List[Profile]):
    """Save all profiles to disk"""
    try:
        with open(PROFILES_FILE, 'w') as f:
            json.dump([profile.model_dump() for profile in profiles], f, indent=2)
    except Exception as e:
        print(f"Error saving profiles: {e}")
        raise

def create_profile(name: str, pin: Optional[str] = None, hint: Optional[str] = None) -> Profile:
    """Create a new profile"""
    profiles = load_profiles()
    profile_id = str(uuid.uuid4())

    new_profile = Profile(
        id=profile_id,
        name=name,
        pin=pin,
        hint=hint,
        is_guest=False,
        created_at=datetime.now().isoformat()
    )

    profiles.append(new_profile)
    save_profiles(profiles)

    # Create profile-specific chat history directory
    profile_chat_dir = CHAT_HISTORY_DIR / profile_id
    profile_chat_dir.mkdir(exist_ok=True)

    # Create profile-specific groups file
    profile_groups_file = CHAT_HISTORY_DIR / profile_id / "groups.json"
    if not profile_groups_file.exists():
        with open(profile_groups_file, 'w') as f:
            json.dump([], f)

    return new_profile

def delete_profile(profile_id: str):
    """Delete a profile and all its data"""
    if profile_id == "guest":
        raise ValueError("Cannot delete guest profile")

    profiles = load_profiles()
    profiles = [p for p in profiles if p.id != profile_id]
    save_profiles(profiles)

    # Delete profile's chat history
    profile_chat_dir = CHAT_HISTORY_DIR / profile_id
    if profile_chat_dir.exists():
        shutil.rmtree(profile_chat_dir)

def validate_profile_pin(profile_id: str, pin: Optional[str]) -> bool:
    """Validate a profile's PIN"""
    profiles = load_profiles()
    for profile in profiles:
        if profile.id == profile_id:
            # If profile has no PIN, any value is valid
            if profile.pin is None:
                return True
            # If profile has PIN, it must match
            return profile.pin == pin
    return False

# Initialize profiles (create guest if needed)
load_profiles()

# Initialize access control - sync documents from attachments directory
access_control.sync_documents_from_directory(ATTACHMENTS_DIR)

# Chat History Management Functions
def get_profile_chat_dir(profile_id: str) -> Path:
    """Get the chat history directory for a profile"""
    profile_dir = CHAT_HISTORY_DIR / profile_id
    profile_dir.mkdir(exist_ok=True)
    return profile_dir

def get_profile_groups_file(profile_id: str) -> Path:
    """Get the groups file for a profile"""
    groups_file = get_profile_chat_dir(profile_id) / "groups.json"
    if not groups_file.exists():
        with open(groups_file, 'w') as f:
            json.dump([], f)
    return groups_file

def get_chat_file_path(profile_id: str, chat_id: str) -> Path:
    """Get the file path for a chat session"""
    return get_profile_chat_dir(profile_id) / f"{chat_id}.json"

def load_chat_session(profile_id: str, chat_id: str) -> Optional[ChatSession]:
    """Load a chat session from disk"""
    file_path = get_chat_file_path(profile_id, chat_id)
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return ChatSession(**data)
    except Exception as e:
        print(f"Error loading chat session {chat_id}: {e}")
        return None

def save_chat_session(profile_id: str, chat_session: ChatSession):
    """Save a chat session to disk"""
    file_path = get_chat_file_path(profile_id, chat_session.id)
    try:
        with open(file_path, 'w') as f:
            json.dump(chat_session.model_dump(), f, indent=2)
    except Exception as e:
        print(f"Error saving chat session {chat_session.id}: {e}")
        raise

def get_all_chat_sessions(profile_id: str) -> List[ChatSession]:
    """Get all chat sessions for a profile (metadata only, without full message history)"""
    sessions = []
    chat_dir = get_profile_chat_dir(profile_id)
    for file_path in chat_dir.glob("*.json"):
        # Skip groups.json
        if file_path.name == "groups.json":
            continue
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Return session with limited message preview
                session = ChatSession(**data)
                # Keep only last message for preview
                if session.messages:
                    session.messages = [session.messages[-1]]
                sessions.append(session)
        except Exception as e:
            print(f"Error loading chat session from {file_path}: {e}")
            continue

    # Sort by updated_at descending
    sessions.sort(key=lambda x: x.updated_at, reverse=True)
    return sessions

def create_new_chat_session(profile_id: str, title: str = "New Chat", group_id: Optional[str] = None) -> ChatSession:
    """Create a new chat session"""
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    session = ChatSession(
        id=chat_id,
        title=title,
        created_at=now,
        updated_at=now,
        messages=[],
        group_id=group_id
    )

    save_chat_session(profile_id, session)
    return session

def add_message_to_chat(profile_id: str, chat_id: str, role: str, content: str, sources: List[str] = []) -> ChatSession:
    """Add a message to a chat session"""
    session = load_chat_session(profile_id, chat_id)
    if not session:
        raise ValueError(f"Chat session {chat_id} not found")

    message = ChatMessage(
        role=role,
        content=content,
        sources=sources,
        timestamp=datetime.now().isoformat()
    )

    session.messages.append(message)
    session.updated_at = datetime.now().isoformat()

    # Auto-generate title from first user message if still "New Chat"
    if session.title == "New Chat" and role == "user" and len(session.messages) == 1:
        # Use first 50 characters of first message as title
        session.title = content[:50] + ("..." if len(content) > 50 else "")

    save_chat_session(profile_id, session)
    return session

def delete_chat_session(profile_id: str, chat_id: str):
    """Delete a chat session"""
    file_path = get_chat_file_path(profile_id, chat_id)
    if file_path.exists():
        file_path.unlink()

def move_chat_to_group(profile_id: str, chat_id: str, group_id: Optional[str]):
    """Move a chat to a different group"""
    session = load_chat_session(profile_id, chat_id)
    if not session:
        raise ValueError(f"Chat session {chat_id} not found")

    session.group_id = group_id
    session.updated_at = datetime.now().isoformat()
    save_chat_session(profile_id, session)
    return session

# Group Management Functions
def load_groups(profile_id: str) -> List[Group]:
    """Load all groups for a profile from disk"""
    groups_file = get_profile_groups_file(profile_id)

    try:
        with open(groups_file, 'r') as f:
            data = json.load(f)
            return [Group(**group) for group in data]
    except Exception as e:
        print(f"Error loading groups: {e}")
        return []

def save_groups(profile_id: str, groups: List[Group]):
    """Save all groups for a profile to disk"""
    groups_file = get_profile_groups_file(profile_id)
    try:
        with open(groups_file, 'w') as f:
            json.dump([group.model_dump() for group in groups], f, indent=2)
    except Exception as e:
        print(f"Error saving groups: {e}")
        raise

def create_group(profile_id: str, name: str) -> Group:
    """Create a new group for a profile"""
    groups = load_groups(profile_id)
    group_id = str(uuid.uuid4())

    new_group = Group(
        id=group_id,
        name=name,
        created_at=datetime.now().isoformat(),
        order=len(groups)  # Add at the end
    )

    groups.append(new_group)
    save_groups(profile_id, groups)
    return new_group

def update_group(profile_id: str, group_id: str, name: str) -> Group:
    """Update a group's name"""
    groups = load_groups(profile_id)

    for group in groups:
        if group.id == group_id:
            group.name = name
            save_groups(profile_id, groups)
            return group

    raise ValueError(f"Group {group_id} not found")

def delete_group(profile_id: str, group_id: str):
    """Delete a group and unassign all chats from it"""
    groups = load_groups(profile_id)
    groups = [g for g in groups if g.id != group_id]
    save_groups(profile_id, groups)

    # Unassign all chats from this group
    chat_dir = get_profile_chat_dir(profile_id)
    for file_path in chat_dir.glob("*.json"):
        if file_path.name == "groups.json":
            continue
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                session = ChatSession(**data)

                if session.group_id == group_id:
                    session.group_id = None
                    save_chat_session(profile_id, session)
        except Exception as e:
            print(f"Error updating chat {file_path}: {e}")
            continue

def get_groups_with_chats(profile_id: str) -> dict:
    """Get all groups with their associated chats for a profile"""
    groups = load_groups(profile_id)
    sessions = get_all_chat_sessions(profile_id)

    # Organize chats by group
    result = {
        "groups": [],
        "ungrouped": []
    }

    # Create a map of group_id to chats
    group_chats = {}
    for session in sessions:
        if session.group_id:
            if session.group_id not in group_chats:
                group_chats[session.group_id] = []
            group_chats[session.group_id].append(session)
        else:
            result["ungrouped"].append(session)

    # Build the result with groups and their chats
    for group in sorted(groups, key=lambda x: x.order):
        result["groups"].append({
            "group": group,
            "chats": group_chats.get(group.id, [])
        })

    return result

# API Endpoints
@app.get("/")
async def root():
    """Serve the frontend HTML"""
    return FileResponse("static/index.html")

@app.get("/admin")
async def admin_portal():
    """Serve the IT admin portal"""
    return FileResponse("static/admin.html")

@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question and get an answer based on the document context
    """
    try:
        if not request.question or request.question.strip() == "":
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        # Save user question to chat history if chat_id provided
        if request.chat_id:
            try:
                add_message_to_chat(request.profile_id, request.chat_id, "user", request.question, [])
            except ValueError:
                raise HTTPException(status_code=404, detail=f"Chat session not found")

        # Retrieve relevant documents
        docs = retriever.invoke(request.question)

        # Filter documents based on user access level
        user_access_profile = access_control.get_user_access_profile(request.profile_id)
        if user_access_profile:
            accessible_docs = access_control.get_user_accessible_documents(request.profile_id)
            accessible_filenames = {doc.filename for doc in accessible_docs}

            # Filter retrieved docs to only include accessible ones
            docs = [
                doc for doc in docs
                if hasattr(doc, 'metadata') and
                'source' in doc.metadata and
                os.path.basename(doc.metadata['source']) in accessible_filenames
            ]

        if not docs:
            answer = "I couldn't find any relevant information in the documents to answer your question."
            sources = []

            # Save assistant response to chat history
            if request.chat_id:
                add_message_to_chat(request.profile_id, request.chat_id, "assistant", answer, sources)

            return QuestionResponse(answer=answer, sources=sources)

        # Format context from documents
        context = "\n\n".join([doc.page_content for doc in docs])

        # Generate answer using LLM
        result = chain.invoke({"context": context, "input": request.question})

        # Extract sources
        sources = []
        for doc in docs:
            if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                source = os.path.basename(doc.metadata['source'])
                if source not in sources:
                    sources.append(source)

        # Save assistant response to chat history
        if request.chat_id:
            add_message_to_chat(request.profile_id, request.chat_id, "assistant", result, sources)

        return QuestionResponse(answer=result, sources=sources)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, CSV, or DOCX) for processing
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.csv', '.docx']
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Save file to attachments directory
        file_path = ATTACHMENTS_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the new document
        process_documents()

        return {
            "status": "success",
            "filename": file.filename,
            "message": f"File '{file.filename}' uploaded and processed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/api/documents")
async def list_documents(profile_id: Optional[str] = None):
    """
    List all documents accessible by the user (respects access control)
    """
    try:
        # If profile_id provided, filter by access level
        if profile_id:
            accessible_docs = access_control.get_user_accessible_documents(profile_id)
            documents = []
            for doc in accessible_docs:
                file_path = Path(doc.file_path)
                if file_path.exists():
                    documents.append({
                        "id": doc.id,
                        "name": doc.filename,
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix.lower(),
                        "access_level": doc.access_level
                    })
        else:
            # No profile_id - show all documents (for admin)
            documents = []
            for file_path in ATTACHMENTS_DIR.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.csv', '.docx']:
                    documents.append({
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix.lower()
                    })

        return {"documents": documents}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/api/documents/{filename}")
async def delete_document(filename: str):
    """
    Delete a document from the attachments directory
    """
    try:
        file_path = ATTACHMENTS_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")

        file_path.unlink()

        # Reprocess documents after deletion
        process_documents()

        return {
            "status": "success",
            "message": f"Document '{filename}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """
    Get the status of the application and vector database
    """
    try:
        # Count documents
        doc_count = len([f for f in ATTACHMENTS_DIR.iterdir()
                        if f.is_file() and f.suffix.lower() in ['.pdf', '.csv', '.docx']])

        # Check vector store status
        vector_store = get_vector_store()
        vector_status = "active" if vector_store else "inactive"

        return StatusResponse(
            status="running",
            documents_count=doc_count,
            vector_db_status=vector_status
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

# Chat Session Endpoints
@app.post("/api/chats", response_model=ChatSession)
async def create_chat(request: CreateChatRequest, profile_id: str):
    """
    Create a new chat session for a profile
    """
    try:
        session = create_new_chat_session(profile_id, request.title, request.group_id)
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chat session: {str(e)}")

@app.get("/api/chats", response_model=List[ChatSession])
async def get_chats(profile_id: str):
    """
    Get all chat sessions for a profile (with preview of last message)
    """
    try:
        sessions = get_all_chat_sessions(profile_id)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat sessions: {str(e)}")

@app.get("/api/chats/{chat_id}", response_model=ChatSession)
async def get_chat(chat_id: str, profile_id: str):
    """
    Get a specific chat session with full message history
    """
    try:
        session = load_chat_session(profile_id, chat_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat session: {str(e)}")

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str, profile_id: str):
    """
    Delete a chat session
    """
    try:
        session = load_chat_session(profile_id, chat_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        delete_chat_session(profile_id, chat_id)

        return {
            "status": "success",
            "message": f"Chat session deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting chat session: {str(e)}")

@app.put("/api/chats/{chat_id}/move")
async def move_chat(chat_id: str, profile_id: str, request: MoveChatRequest):
    """
    Move a chat to a different group
    """
    try:
        session = move_chat_to_group(profile_id, chat_id, request.group_id)
        return {
            "status": "success",
            "message": "Chat moved successfully",
            "chat": session
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving chat: {str(e)}")

# Group Endpoints
@app.get("/api/groups")
async def get_all_groups(profile_id: str):
    """
    Get all groups for a profile
    """
    try:
        groups = load_groups(profile_id)
        return {"groups": groups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting groups: {str(e)}")

@app.get("/api/groups/with-chats")
async def get_groups_and_chats(profile_id: str):
    """
    Get all groups with their associated chats for a profile
    """
    try:
        result = get_groups_with_chats(profile_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting groups with chats: {str(e)}")

@app.post("/api/groups", response_model=Group)
async def create_new_group(request: CreateGroupRequest, profile_id: str):
    """
    Create a new group for a profile
    """
    try:
        group = create_group(profile_id, request.name)
        return group
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating group: {str(e)}")

@app.put("/api/groups/{group_id}", response_model=Group)
async def update_group_name(group_id: str, profile_id: str, request: UpdateGroupRequest):
    """
    Update a group's name
    """
    try:
        group = update_group(profile_id, group_id, request.name)
        return group
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating group: {str(e)}")

@app.delete("/api/groups/{group_id}")
async def delete_existing_group(group_id: str, profile_id: str):
    """
    Delete a group
    """
    try:
        delete_group(profile_id, group_id)
        return {
            "status": "success",
            "message": "Group deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting group: {str(e)}")

# Chat Transfer Function
def transfer_chats_between_profiles(from_profile_id: str, to_profile_id: str):
    """Transfer all chats and groups from one profile to another"""
    from_chat_dir = get_profile_chat_dir(from_profile_id)
    to_chat_dir = get_profile_chat_dir(to_profile_id)

    # Transfer all chat files
    for chat_file in from_chat_dir.glob("*.json"):
        if chat_file.name == "groups.json":
            continue

        # Move chat file to new profile
        destination = to_chat_dir / chat_file.name
        shutil.copy2(chat_file, destination)
        chat_file.unlink()

    # Transfer groups
    from_groups_file = get_profile_groups_file(from_profile_id)
    to_groups_file = get_profile_groups_file(to_profile_id)

    if from_groups_file.exists():
        with open(from_groups_file, 'r') as f:
            from_groups = json.load(f)

        with open(to_groups_file, 'r') as f:
            to_groups = json.load(f)

        # Merge groups (append from_groups to to_groups)
        to_groups.extend(from_groups)

        with open(to_groups_file, 'w') as f:
            json.dump(to_groups, f, indent=2)

        # Clear from_groups
        with open(from_groups_file, 'w') as f:
            json.dump([], f)

# Profile Endpoints
@app.get("/api/profiles", response_model=List[Profile])
async def get_all_profiles():
    """
    Get all profiles (without PIN information for security)
    """
    try:
        profiles = load_profiles()
        # Set has_pin flag and remove PIN from response for security
        for profile in profiles:
            profile.has_pin = profile.pin is not None and profile.pin != ""
            profile.pin = None
        return profiles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting profiles: {str(e)}")

@app.post("/api/profiles", response_model=Profile)
async def create_new_profile(request: CreateProfileRequest):
    """
    Create a new profile
    """
    try:
        profile = create_profile(request.name, request.pin, request.hint)
        # Set has_pin flag and remove PIN from response for security
        profile.has_pin = profile.pin is not None and profile.pin != ""
        profile.pin = None
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")

@app.post("/api/profiles/{to_profile_id}/transfer")
async def transfer_chats(to_profile_id: str, from_profile_id: str):
    """
    Transfer all chats from one profile to another
    """
    try:
        transfer_chats_between_profiles(from_profile_id, to_profile_id)
        return {
            "status": "success",
            "message": f"Chats transferred successfully from profile {from_profile_id} to {to_profile_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transferring chats: {str(e)}")

@app.post("/api/profiles/login")
async def login_profile(request: LoginProfileRequest):
    """
    Validate profile PIN and login
    """
    try:
        is_valid = validate_profile_pin(request.profile_id, request.pin)
        if is_valid:
            # Get profile details
            profiles = load_profiles()
            profile = next((p for p in profiles if p.id == request.profile_id), None)
            if profile:
                # Remove PIN from response
                profile.pin = None
                return {
                    "status": "success",
                    "message": "Login successful",
                    "profile": profile
                }
        raise HTTPException(status_code=401, detail="Invalid PIN")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging in: {str(e)}")

@app.get("/api/profiles/{profile_id}/hint")
async def get_profile_hint(profile_id: str):
    """
    Get the password hint for a profile
    """
    try:
        profiles = load_profiles()
        profile = next((p for p in profiles if p.id == profile_id), None)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {
            "hint": profile.hint if profile.hint else "No hint available"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting hint: {str(e)}")

@app.delete("/api/profiles/{profile_id}")
async def delete_existing_profile(profile_id: str):
    """
    Delete a profile and all its data
    """
    try:
        delete_profile(profile_id)
        return {
            "status": "success",
            "message": "Profile deleted successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting profile: {str(e)}")

@app.put("/api/profiles/{profile_id}")
async def update_profile(profile_id: str, request: UpdateProfileRequest):
    """
    Update profile information (name, pin, hint)
    """
    try:
        profiles = load_profiles()
        profile = None

        for p in profiles:
            if p.id == profile_id:
                profile = p
                break

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        if profile.is_guest:
            raise HTTPException(status_code=400, detail="Cannot update guest profile")

        # Update fields if provided
        if request.name is not None:
            profile.name = request.name
        if request.pin is not None:
            profile.pin = request.pin
        if request.hint is not None:
            profile.hint = request.hint

        # Save updated profiles
        save_profiles(profiles)

        # Return profile without PIN for security
        profile.has_pin = profile.pin is not None and profile.pin != ""
        profile.pin = None

        return {
            "status": "success",
            "message": "Profile updated successfully",
            "profile": profile
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

@app.post("/api/profiles/{profile_id}/picture")
async def upload_profile_picture(profile_id: str, file: UploadFile = File(...)):
    """
    Upload a profile picture for a user
    """
    try:
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )

        # Load profiles
        profiles = load_profiles()
        profile = None

        for p in profiles:
            if p.id == profile_id:
                profile = p
                break

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Delete old profile picture if exists
        if profile.profile_picture:
            old_pic_path = Path(profile.profile_picture)
            if old_pic_path.exists():
                old_pic_path.unlink()

        # Save new profile picture
        filename = f"{profile_id}{file_ext}"
        file_path = PROFILE_PICTURES_DIR / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update profile with picture path
        profile.profile_picture = str(file_path)
        save_profiles(profiles)

        return {
            "status": "success",
            "message": "Profile picture uploaded successfully",
            "picture_url": f"/profile_pictures/{filename}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading profile picture: {str(e)}")

@app.get("/api/profiles/{profile_id}/picture")
async def get_profile_picture(profile_id: str):
    """
    Get profile picture for a user
    """
    try:
        profiles = load_profiles()
        profile = None

        for p in profiles:
            if p.id == profile_id:
                profile = p
                break

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        if not profile.profile_picture or not Path(profile.profile_picture).exists():
            # Return default avatar
            raise HTTPException(status_code=404, detail="No profile picture found")

        return FileResponse(profile.profile_picture)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting profile picture: {str(e)}")

@app.delete("/api/profiles/{profile_id}/picture")
async def delete_profile_picture(profile_id: str):
    """
    Delete profile picture for a user
    """
    try:
        profiles = load_profiles()
        profile = None

        for p in profiles:
            if p.id == profile_id:
                profile = p
                break

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        if profile.profile_picture:
            pic_path = Path(profile.profile_picture)
            if pic_path.exists():
                pic_path.unlink()

            profile.profile_picture = None
            save_profiles(profiles)

        return {
            "status": "success",
            "message": "Profile picture deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting profile picture: {str(e)}")

# ============================================================================
# ACCESS CONTROL ENDPOINTS
# ============================================================================

# IT Admin Authentication Endpoints
@app.post("/api/admin/login")
async def admin_login(request: ITAdminLoginRequest):
    """
    Authenticate IT administrator
    """
    try:
        admin = access_control.authenticate_admin(request.username, request.password)
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "status": "success",
            "message": "Admin login successful",
            "admin": {
                "id": admin.id,
                "username": admin.username
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during admin login: {str(e)}")

@app.post("/api/admin/create")
async def create_admin(request: CreateITAdminRequest):
    """
    Create a new IT admin account (requires existing admin authentication in production)
    """
    try:
        admin = access_control.create_it_admin(request.username, request.password)
        return {
            "status": "success",
            "message": "Admin created successfully",
            "admin": {
                "id": admin.id,
                "username": admin.username
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating admin: {str(e)}")

@app.get("/api/admin/list")
async def list_admins():
    """
    List all IT admin accounts
    """
    try:
        admins = access_control.get_all_admins()
        return {
            "admins": [
                {"id": admin.id, "username": admin.username, "created_at": admin.created_at}
                for admin in admins
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing admins: {str(e)}")

# Document Access Management Endpoints
@app.get("/api/admin/documents")
async def get_all_managed_documents():
    """
    Get all documents with their access levels (for admin dashboard)
    """
    try:
        documents = access_control.get_all_documents()
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_path": doc.file_path,
                    "access_level": doc.access_level,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at
                }
                for doc in documents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting documents: {str(e)}")

@app.put("/api/admin/documents/{doc_id}/access-level")
async def update_document_access(doc_id: str, request: UpdateDocumentAccessRequest):
    """
    Update the access level required for a document
    """
    try:
        doc = access_control.update_document_access_level(doc_id, request.access_level)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "status": "success",
            "message": "Document access level updated",
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "access_level": doc.access_level
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

@app.post("/api/admin/documents/sync")
async def sync_documents():
    """
    Sync documents from attachments directory with access control system
    """
    try:
        access_control.sync_documents_from_directory(ATTACHMENTS_DIR)
        documents = access_control.get_all_documents()
        return {
            "status": "success",
            "message": f"Synced {len(documents)} documents",
            "total_documents": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing documents: {str(e)}")

# User Access Management Endpoints
@app.post("/api/admin/users/{user_id}/access-level")
async def assign_user_access_level(user_id: str, request: AssignAccessLevelRequest):
    """
    Assign or update a user's access level
    """
    try:
        # Check if user exists in profiles
        profiles = load_profiles()
        user_exists = any(p.id == user_id for p in profiles)
        if not user_exists:
            raise HTTPException(status_code=404, detail="User profile not found")

        # Check if user already has an access profile
        existing_profile = access_control.get_user_access_profile(user_id)

        if existing_profile:
            # Update existing access level
            user_profile = access_control.update_user_access_level(user_id, request.access_level)
        else:
            # Create new access profile
            user_profile = access_control.create_user_access_profile(user_id, request.access_level)

        return {
            "status": "success",
            "message": "User access level assigned",
            "user_profile": {
                "user_id": user_profile.user_id,
                "access_level": user_profile.access_level,
                "allowed_documents_count": len(user_profile.allowed_documents)
            }
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning access level: {str(e)}")

@app.post("/api/admin/users/{user_id}/assign-documents")
async def assign_user_documents(user_id: str, request: AssignDocumentsRequest):
    """
    Manually assign specific documents to a user (for Level 2 custom access)
    """
    try:
        user_profile = access_control.assign_documents_to_user(user_id, request.document_ids)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User access profile not found")

        return {
            "status": "success",
            "message": "Documents assigned to user",
            "user_profile": {
                "user_id": user_profile.user_id,
                "access_level": user_profile.access_level,
                "allowed_documents": user_profile.allowed_documents
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning documents: {str(e)}")

@app.get("/api/admin/users")
async def get_all_user_access_profiles():
    """
    Get all users with their access profiles (for admin dashboard)
    """
    try:
        profiles = load_profiles()
        user_access_data = []

        for profile in profiles:
            access_profile = access_control.get_user_access_profile(profile.id)
            accessible_docs = access_control.get_user_accessible_documents(profile.id) if access_profile else []

            user_access_data.append({
                "user_id": profile.id,
                "username": profile.name,
                "is_guest": profile.is_guest,
                "access_level": access_profile.access_level if access_profile else None,
                "accessible_documents_count": len(accessible_docs),
                "accessible_documents": [
                    {"id": doc.id, "filename": doc.filename}
                    for doc in accessible_docs
                ]
            })

        return {"users": user_access_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user access profiles: {str(e)}")

@app.get("/api/admin/users/{user_id}/access")
async def get_user_access_details(user_id: str):
    """
    Get detailed access information for a specific user
    """
    try:
        access_profile = access_control.get_user_access_profile(user_id)
        if not access_profile:
            return {
                "user_id": user_id,
                "has_access_profile": False,
                "access_level": None,
                "accessible_documents": []
            }

        accessible_docs = access_control.get_user_accessible_documents(user_id)

        return {
            "user_id": user_id,
            "has_access_profile": True,
            "access_level": access_profile.access_level,
            "allowed_documents": access_profile.allowed_documents,
            "accessible_documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "access_level": doc.access_level
                }
                for doc in accessible_docs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user access details: {str(e)}")

@app.get("/api/admin/statistics")
async def get_access_statistics():
    """
    Get statistics about the access control system
    """
    try:
        stats = access_control.get_access_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

# User-facing access endpoints
@app.get("/api/users/{user_id}/accessible-documents")
async def get_user_accessible_docs(user_id: str):
    """
    Get documents accessible to a specific user (for frontend display)
    """
    try:
        accessible_docs = access_control.get_user_accessible_documents(user_id)
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "access_level_required": doc.access_level
                }
                for doc in accessible_docs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting accessible documents: {str(e)}")

@app.get("/api/users/{user_id}/access-info")
async def get_user_access_info(user_id: str):
    """
    Get access level information for a user
    """
    try:
        access_profile = access_control.get_user_access_profile(user_id)

        if not access_profile:
            return {
                "user_id": user_id,
                "has_access": False,
                "access_level": None,
                "access_level_name": "No Access"
            }

        level_names = {
            ACCESS_LEVEL_1: "Level 1 - Single Document",
            ACCESS_LEVEL_2: "Level 2 - Multiple Documents",
            ACCESS_LEVEL_3: "Level 3 - All Documents",
            ACCESS_LEVEL_ADMIN: "Administrator"
        }

        return {
            "user_id": user_id,
            "has_access": True,
            "access_level": access_profile.access_level,
            "access_level_name": level_names.get(access_profile.access_level, "Unknown"),
            "document_count": len(access_profile.allowed_documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting access info: {str(e)}")

# Mount static files and profile pictures
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/profile_pictures", StaticFiles(directory="profile_pictures"), name="profile_pictures")

if __name__ == "__main__":
    print("Starting Local AI Agent API server...")
    print("Access the web interface at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
