"""
Access Control System for Document Management
Manages 3 levels of hierarchical document access with IT admin configuration

Hierarchical Access Model:
- Low Level (1): Access to Low level documents only
- Medium Level (2): Access to Medium + Low level documents
- High Level (3): Access to High + Medium + Low level documents
- Admin (99): Access to all documents

Documents can be assigned to levels, and users automatically inherit access to
documents at their level and all levels below.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import json
from pathlib import Path
import uuid

# Access Levels - All allow manual document selection (1 or more documents)
ACCESS_LEVEL_LOW = 1     # Low Level Access - Select 1 or more documents
ACCESS_LEVEL_MEDIUM = 2  # Medium Level Access - Select 1 or more documents
ACCESS_LEVEL_HIGH = 3    # High Level Access - Select 1 or more documents
ACCESS_LEVEL_ADMIN = 99  # IT Admin - full control

# Legacy level constants (for backwards compatibility)
ACCESS_LEVEL_1 = 1
ACCESS_LEVEL_2 = 2
ACCESS_LEVEL_3 = 3

class DocumentAccess(BaseModel):
    """Represents a document with access control"""
    id: str
    filename: str
    display_name: str
    file_path: str
    access_level: int  # Minimum level required to access this document
    created_at: str
    updated_at: str

class UserAccessProfile(BaseModel):
    """Extended user profile with access level"""
    user_id: str
    access_level: int
    allowed_documents: List[str]  # List of document IDs user can access
    created_at: str
    updated_at: str

class ITAdmin(BaseModel):
    """IT Administrator account"""
    id: str
    username: str
    password_hash: str  # In production, use proper hashing
    created_at: str

class LevelConfiguration(BaseModel):
    """Configuration for access levels and their default documents"""
    level: int
    level_name: str
    default_documents: List[str]  # List of document IDs
    updated_at: str

class AccessControlManager:
    """Manages document access control"""

    def __init__(self):
        self.documents_file = Path("./access_control_documents.json")
        self.user_access_file = Path("./user_access_profiles.json")
        self.it_admins_file = Path("./it_admins.json")
        self.level_config_file = Path("./level_configurations.json")

        self._initialize_files()

    def _initialize_files(self):
        """Initialize access control files if they don't exist"""
        if not self.documents_file.exists():
            self._save_json(self.documents_file, [])

        if not self.user_access_file.exists():
            self._save_json(self.user_access_file, [])

        if not self.it_admins_file.exists():
            # Create default IT admin (username: admin, password: admin123)
            default_admin = ITAdmin(
                id=str(uuid.uuid4()),
                username="admin",
                password_hash="admin123",  # In production, use bcrypt or similar
                created_at=datetime.now().isoformat()
            )
            self._save_json(self.it_admins_file, [default_admin.model_dump()])

        if not self.level_config_file.exists():
            # Create default level configurations
            default_configs = [
                LevelConfiguration(
                    level=ACCESS_LEVEL_LOW,
                    level_name="Low Level Access",
                    default_documents=[],
                    updated_at=datetime.now().isoformat()
                ),
                LevelConfiguration(
                    level=ACCESS_LEVEL_MEDIUM,
                    level_name="Medium Level Access",
                    default_documents=[],
                    updated_at=datetime.now().isoformat()
                ),
                LevelConfiguration(
                    level=ACCESS_LEVEL_HIGH,
                    level_name="High Level Access",
                    default_documents=[],
                    updated_at=datetime.now().isoformat()
                )
            ]
            self._save_json(self.level_config_file, [config.model_dump() for config in default_configs])

    def _load_json(self, file_path: Path) -> list:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []

    def _save_json(self, file_path: Path, data: list):
        """Save JSON data to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving {file_path}: {e}")
            raise

    # Document Management
    def register_document(self, filename: str, file_path: str, access_level: int = ACCESS_LEVEL_3) -> DocumentAccess:
        """Register a new document in the access control system"""
        documents = self._load_json(self.documents_file)

        doc_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        new_doc = DocumentAccess(
            id=doc_id,
            filename=filename,
            display_name=filename,
            file_path=file_path,
            access_level=access_level,
            created_at=now,
            updated_at=now
        )

        documents.append(new_doc.model_dump())
        self._save_json(self.documents_file, documents)
        return new_doc

    def get_all_documents(self) -> List[DocumentAccess]:
        """Get all registered documents"""
        documents = self._load_json(self.documents_file)
        return [DocumentAccess(**doc) for doc in documents]

    def get_document_by_id(self, doc_id: str) -> Optional[DocumentAccess]:
        """Get a document by ID"""
        documents = self._load_json(self.documents_file)
        for doc in documents:
            if doc['id'] == doc_id:
                return DocumentAccess(**doc)
        return None

    def update_document_access_level(self, doc_id: str, access_level: int) -> Optional[DocumentAccess]:
        """Update the access level required for a document"""
        documents = self._load_json(self.documents_file)

        for doc in documents:
            if doc['id'] == doc_id:
                doc['access_level'] = access_level
                doc['updated_at'] = datetime.now().isoformat()
                self._save_json(self.documents_file, documents)
                return DocumentAccess(**doc)

        return None

    def delete_document(self, doc_id: str) -> bool:
        """Remove a document from access control"""
        documents = self._load_json(self.documents_file)
        original_count = len(documents)
        documents = [doc for doc in documents if doc['id'] != doc_id]

        if len(documents) < original_count:
            self._save_json(self.documents_file, documents)
            return True
        return False

    # User Access Management
    def create_user_access_profile(self, user_id: str, access_level: int) -> UserAccessProfile:
        """Create an access profile for a user"""
        user_profiles = self._load_json(self.user_access_file)

        # Check if user already has a profile
        for profile in user_profiles:
            if profile['user_id'] == user_id:
                raise ValueError(f"User {user_id} already has an access profile")

        now = datetime.now().isoformat()

        # Determine allowed documents based on access level
        allowed_docs = self._get_allowed_documents_by_level(access_level)

        new_profile = UserAccessProfile(
            user_id=user_id,
            access_level=access_level,
            allowed_documents=allowed_docs,
            created_at=now,
            updated_at=now
        )

        user_profiles.append(new_profile.model_dump())
        self._save_json(self.user_access_file, user_profiles)
        return new_profile

    def get_user_access_profile(self, user_id: str) -> Optional[UserAccessProfile]:
        """Get a user's access profile"""
        user_profiles = self._load_json(self.user_access_file)
        for profile in user_profiles:
            if profile['user_id'] == user_id:
                return UserAccessProfile(**profile)
        return None

    def update_user_access_level(self, user_id: str, access_level: int) -> Optional[UserAccessProfile]:
        """Update a user's access level"""
        user_profiles = self._load_json(self.user_access_file)

        for profile in user_profiles:
            if profile['user_id'] == user_id:
                profile['access_level'] = access_level
                profile['allowed_documents'] = self._get_allowed_documents_by_level(access_level)
                profile['updated_at'] = datetime.now().isoformat()
                self._save_json(self.user_access_file, user_profiles)
                return UserAccessProfile(**profile)

        return None

    def assign_documents_to_user(self, user_id: str, document_ids: List[str]) -> Optional[UserAccessProfile]:
        """Manually assign specific documents to a user (for all access levels)"""
        user_profiles = self._load_json(self.user_access_file)

        for profile in user_profiles:
            if profile['user_id'] == user_id:
                profile['allowed_documents'] = document_ids
                profile['updated_at'] = datetime.now().isoformat()
                self._save_json(self.user_access_file, user_profiles)
                return UserAccessProfile(**profile)

        return None

    def _get_allowed_documents_by_level(self, access_level: int) -> List[str]:
        """Determine allowed documents based on access level configuration with hierarchical access"""
        documents = self.get_all_documents()

        if access_level == ACCESS_LEVEL_ADMIN:
            # Admin: All documents
            return [doc.id for doc in documents]

        # Hierarchical access: users can access documents at their level and below
        # Low level (1): only Low level documents
        # Medium level (2): Medium + Low level documents
        # High level (3): High + Medium + Low level documents

        allowed_doc_ids = []
        level_configs = self._load_json(self.level_config_file)

        # Get documents for current level and all levels below
        for config in level_configs:
            if config['level'] <= access_level:
                # Add all documents configured for this level and below
                allowed_doc_ids.extend(config.get('default_documents', []))

        # Remove duplicates while preserving order
        return list(dict.fromkeys(allowed_doc_ids))

    def check_document_access(self, user_id: str, doc_id: str) -> bool:
        """Check if a user has access to a specific document (supports hierarchical access)"""
        user_profile = self.get_user_access_profile(user_id)

        if not user_profile:
            # No access profile = no access
            return False

        # Admin has access to everything
        if user_profile.access_level == ACCESS_LEVEL_ADMIN:
            return True

        # Check if document is in user's allowed list (hierarchical access already applied)
        return doc_id in user_profile.allowed_documents

    def get_user_accessible_documents(self, user_id: str) -> List[DocumentAccess]:
        """Get all documents a user can access (supports hierarchical access)"""
        user_profile = self.get_user_access_profile(user_id)

        if not user_profile:
            return []

        all_documents = self.get_all_documents()

        if user_profile.access_level == ACCESS_LEVEL_ADMIN:
            return all_documents

        # Filter documents based on allowed_documents (hierarchical access already applied)
        accessible = [
            doc for doc in all_documents
            if doc.id in user_profile.allowed_documents
        ]

        return accessible

    def get_assignable_documents_for_user(self, user_id: str) -> List[DocumentAccess]:
        """
        Get documents that can be assigned to a user based on their access level.
        Uses hierarchical access: user can be assigned documents at their level and below.
        """
        user_profile = self.get_user_access_profile(user_id)

        if not user_profile:
            return []

        all_documents = self.get_all_documents()

        if user_profile.access_level == ACCESS_LEVEL_ADMIN:
            # Admin can be assigned all documents
            return all_documents

        # User can only be assigned documents at their level or below
        # Low (1) -> only Low docs
        # Medium (2) -> Medium + Low docs
        # High (3) -> High + Medium + Low docs
        assignable = [
            doc for doc in all_documents
            if doc.access_level <= user_profile.access_level
        ]

        return assignable

    # IT Admin Management
    def authenticate_admin(self, username: str, password: str) -> Optional[ITAdmin]:
        """Authenticate an IT admin"""
        admins = self._load_json(self.it_admins_file)

        for admin in admins:
            if admin['username'] == username and admin['password_hash'] == password:
                return ITAdmin(**admin)

        return None

    def create_it_admin(self, username: str, password: str) -> ITAdmin:
        """Create a new IT admin account"""
        admins = self._load_json(self.it_admins_file)

        # Check if username already exists
        for admin in admins:
            if admin['username'] == username:
                raise ValueError(f"Admin username '{username}' already exists")

        new_admin = ITAdmin(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=password,  # In production, hash this properly
            created_at=datetime.now().isoformat()
        )

        admins.append(new_admin.model_dump())
        self._save_json(self.it_admins_file, admins)
        return new_admin

    def get_all_admins(self) -> List[ITAdmin]:
        """Get all IT admin accounts"""
        admins = self._load_json(self.it_admins_file)
        return [ITAdmin(**admin) for admin in admins]

    # Bulk Operations
    def sync_documents_from_directory(self, directory_path: Path):
        """Sync documents from a directory with the access control system"""
        if not directory_path.exists():
            return

        existing_docs = self.get_all_documents()
        existing_filenames = {doc.filename for doc in existing_docs}

        # Add new documents
        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.csv', '.docx']:
                if file_path.name not in existing_filenames:
                    self.register_document(
                        filename=file_path.name,
                        file_path=str(file_path),
                        access_level=ACCESS_LEVEL_3  # Default to Level 3
                    )
                    print(f"Registered new document: {file_path.name}")

    def get_access_statistics(self) -> Dict:
        """Get statistics about the access control system"""
        documents = self.get_all_documents()
        user_profiles = self._load_json(self.user_access_file)
        admins = self.get_all_admins()

        level_counts = {1: 0, 2: 0, 3: 0, 99: 0}
        for profile in user_profiles:
            level = profile['access_level']
            if level in level_counts:
                level_counts[level] += 1

        return {
            "total_documents": len(documents),
            "total_users": len(user_profiles),
            "total_admins": len(admins),
            "users_by_level": {
                "level_1": level_counts[1],
                "level_2": level_counts[2],
                "level_3": level_counts[3],
                "admin": level_counts[99]
            }
        }

    # Level Configuration Methods
    def get_level_configurations(self) -> List[LevelConfiguration]:
        """Get all level configurations"""
        configs = self._load_json(self.level_config_file)
        return [LevelConfiguration(**config) for config in configs]

    def get_level_configuration(self, level: int) -> Optional[LevelConfiguration]:
        """Get configuration for a specific level"""
        configs = self._load_json(self.level_config_file)
        for config in configs:
            if config['level'] == level:
                return LevelConfiguration(**config)
        return None

    def update_level_configuration(self, level: int, document_ids: List[str]) -> Optional[LevelConfiguration]:
        """Update the default documents for a level"""
        configs = self._load_json(self.level_config_file)

        for config in configs:
            if config['level'] == level:
                config['default_documents'] = document_ids
                config['updated_at'] = datetime.now().isoformat()
                self._save_json(self.level_config_file, configs)
                return LevelConfiguration(**config)

        return None


# Global instance
access_control = AccessControlManager()
