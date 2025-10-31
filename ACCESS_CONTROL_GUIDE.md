# Access Control System Guide

## Overview

This document management system now includes a comprehensive 3-level access control system that allows administrators to control which documents users can access and query.

## Access Levels

### Level 1 - Single Document Access
- Users can only access **one document** (the first/top-level document)
- Ideal for basic users who need limited information
- Queries will only return results from their assigned single document

### Level 2 - Multiple Documents Access
- Users can access **multiple selected documents**
- Can be manually configured by IT admins
- By default, gets access to approximately half the documents
- Flexible for departmental or team-based access

### Level 3 - Full Access
- Users can access **all documents** in the system
- Suitable for managers and senior staff
- No restrictions on document queries

### Level 99 - Administrator
- Full system access including all documents
- Can be assigned to IT personnel
- Same access as Level 3 for documents

## System Components

### 1. Access Control Manager (`access_control.py`)
The core access control logic that manages:
- Document registration and access levels
- User access profiles
- IT admin authentication
- Access validation

### 2. API Endpoints (in `app.py`)
Extended API with access control endpoints:

#### IT Admin Endpoints
- `POST /api/admin/login` - Admin authentication
- `POST /api/admin/create` - Create new admin account
- `GET /api/admin/list` - List all admins
- `GET /api/admin/statistics` - System statistics
- `GET /api/admin/users` - List all users with access info
- `POST /api/admin/users/{user_id}/access-level` - Assign access level
- `POST /api/admin/users/{user_id}/assign-documents` - Assign specific documents
- `GET /api/admin/documents` - List all documents with access levels
- `PUT /api/admin/documents/{doc_id}/access-level` - Update document access level
- `POST /api/admin/documents/sync` - Sync documents from filesystem

#### User Endpoints
- `GET /api/users/{user_id}/accessible-documents` - Get user's accessible documents
- `GET /api/users/{user_id}/access-info` - Get user's access level info
- `GET /api/documents?profile_id={id}` - List documents (filtered by access)

### 3. IT Admin Portal (`/admin`)
A web-based admin interface accessible at `http://localhost:8000/admin`

**Default credentials:**
- Username: `admin`
- Password: `admin123`

**Features:**
- Dashboard with statistics
- User management (assign access levels)
- Document management (set access requirements)
- Manual document assignment for Level 2 users
- Document synchronization

## Setup and Usage

### 1. Start the Server
```bash
python app.py
```

The server starts at `http://localhost:8000`

### 2. Access the Admin Portal
Navigate to `http://localhost:8000/admin` and login with default credentials.

### 3. Initialize Documents
1. Upload documents via the main interface or place them in `attachments/` folder
2. In admin portal, click "Sync Documents" to register them in access control
3. All new documents default to Level 3 access requirement

### 4. Assign User Access Levels

#### Via Admin Portal:
1. Go to "User Management" tab
2. Click "Set Level" for any user
3. Select access level (1, 2, 3, or Admin)
4. Submit

#### Via API:
```bash
curl -X POST http://localhost:8000/api/admin/users/{user_id}/access-level \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid", "access_level": 2}'
```

### 5. Assign Specific Documents (Level 2)
For fine-grained control:

1. Assign user to Level 2
2. Click "Assign Docs" button
3. Select specific documents
4. Submit

### 6. Manage Document Access Levels
Control which level can access each document:

1. Go to "Document Management" tab
2. Click "Change Level" for a document
3. Set minimum access level required (1, 2, or 3)
4. Submit

## Access Control Flow

### When a User Queries Documents:

1. User submits a question via `/api/ask`
2. System retrieves relevant documents from vector database
3. **Access Control Filter Applied:**
   - Loads user's access profile
   - Gets list of documents user can access
   - Filters retrieved documents to only include accessible ones
4. Filtered documents are used to generate the answer
5. User only sees information from their accessible documents

### Document Access Check:
```
User makes query
    ↓
Retrieve from vector DB
    ↓
Check user access profile
    ↓
Filter by allowed documents
    ↓
Generate answer from filtered docs
    ↓
Return to user
```

## Data Files

The system creates several JSON files for persistence:

- `access_control_documents.json` - Document registry with access levels
- `user_access_profiles.json` - User access level assignments
- `it_admins.json` - IT administrator accounts
- `profiles.json` - User profiles (existing)

## API Examples

### 1. Create a New Admin
```bash
curl -X POST http://localhost:8000/api/admin/create \
  -H "Content-Type: application/json" \
  -d '{"username": "newadmin", "password": "secure123"}'
```

### 2. Assign Level 1 Access to User
```bash
curl -X POST http://localhost:8000/api/admin/users/b5b48291-a8e3-4876-b0fc-123937a3d914/access-level \
  -H "Content-Type: application/json" \
  -d '{"user_id": "b5b48291-a8e3-4876-b0fc-123937a3d914", "access_level": 1}'
```

### 3. Check User's Accessible Documents
```bash
curl http://localhost:8000/api/users/b5b48291-a8e3-4876-b0fc-123937a3d914/accessible-documents
```

### 4. Update Document to Require Level 2
```bash
curl -X PUT http://localhost:8000/api/admin/documents/{doc_id}/access-level \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-uuid", "access_level": 2}'
```

### 5. Get System Statistics
```bash
curl http://localhost:8000/api/admin/statistics
```

## Security Considerations

### Current Implementation (Development)
- Plain text password storage for admins
- No session management/JWT tokens
- No rate limiting

### Production Recommendations
1. **Password Hashing**: Use `bcrypt` or `argon2` for admin passwords
2. **Session Management**: Implement JWT tokens with expiration
3. **HTTPS**: Use SSL/TLS for all admin communications
4. **Rate Limiting**: Add rate limiting to prevent brute force attacks
5. **Audit Logging**: Log all access control changes
6. **Multi-Factor Authentication**: For admin accounts

## Example Workflow

### Scenario: Setting up access for a new team

1. **Create User Profiles** (existing functionality)
   - Create profiles for team members

2. **Assign Access Levels**
   ```
   Team Lead → Level 3 (all documents)
   Senior Members → Level 2 (selected documents)
   Junior Members → Level 1 (single document)
   ```

3. **Configure Level 2 Users**
   - Select specific documents relevant to their role
   - For example: HR documents for HR team, Finance docs for Finance team

4. **Test Access**
   - Login as each user
   - Try querying different topics
   - Verify they only get answers from their accessible documents

## Troubleshooting

### Documents not showing up in admin portal
- Click "Sync Documents" button in Document Management tab
- Ensure documents are in `attachments/` directory
- Check file extensions are `.pdf`, `.csv`, or `.docx`

### User can't access any documents
- Check user has been assigned an access level
- Verify in User Management tab of admin portal
- Check `user_access_profiles.json` for user entry

### Admin login not working
- Default credentials: `admin` / `admin123`
- Check `it_admins.json` file exists
- Create new admin via API if needed

### Access control not filtering documents
- Ensure user has an access profile (not just a user profile)
- Check that documents are registered in `access_control_documents.json`
- Run document sync if documents were added manually

## Migration from Existing System

If you have existing users:

1. **Sync all documents**: Use "Sync Documents" in admin portal
2. **Assign default access**: Decide default level for existing users
3. **Bulk assign**: Use API to assign access levels to all existing users
4. **Test thoroughly**: Verify each user's access before going live

## Future Enhancements

Possible additions to the access control system:

- Role-based access control (RBAC) with custom roles
- Time-based access (temporary access grants)
- Document categories/tags for easier management
- Access request workflow (users request access, admins approve)
- Detailed audit logs and access reports
- Group-based access (assign access to groups instead of individuals)
- Document versioning with access control
- Export/import access configurations

## Support

For issues or questions about the access control system:
1. Check this documentation
2. Review API endpoint documentation
3. Check log files for error messages
4. Verify JSON data files for corruption
