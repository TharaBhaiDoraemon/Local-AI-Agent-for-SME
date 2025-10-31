# Quick Start Guide - 3-Level Access Control System

## What's New?

Your document management system now has a powerful 3-level access control system:

- **Level 1**: Access to a single document (top file)
- **Level 2**: Access to multiple selected documents
- **Level 3**: Access to all documents
- **IT Admin**: Separate portal to manage all access levels

## Quick Setup (5 Minutes)

### Step 1: Start the Server
```bash
python app.py
```

Server will start at `http://localhost:8000`

### Step 2: Access the Admin Portal
Open your browser and go to: **http://localhost:8000/admin**

**Login credentials:**
- Username: `admin`
- Password: `admin123`

### Step 3: Sync Your Documents
1. Click the **"Sync Documents"** button in the Document Management tab
2. This registers all PDF/DOCX/CSV files from the `attachments/` folder

### Step 4: Assign Access Levels to Users
1. Go to the **"User Management"** tab
2. For each user, click **"Set Level"**
3. Choose their access level:
   - Level 1 for basic users (1 document)
   - Level 2 for team members (selected documents)
   - Level 3 for managers (all documents)

### Step 5: Test It Out!
1. Login as a user in the main app (`http://localhost:8000`)
2. Try asking questions
3. Users will only get answers from their accessible documents!

## Testing the System

Run the automated test suite:
```bash
python test_access_control.py
```

This will test all 3 access levels and verify the system works correctly.

## Key Features

### For IT Admins (via `/admin` portal):
- ✅ View system statistics (users, documents, access levels)
- ✅ Assign access levels to users (1, 2, 3, or Admin)
- ✅ Manually select which documents Level 2 users can access
- ✅ Set minimum access level required for each document
- ✅ Sync new documents automatically

### For Regular Users:
- ✅ Automatic filtering - only queries accessible documents
- ✅ See which documents they have access to
- ✅ No access to documents above their level

## Example Use Cases

### Scenario 1: Department-Based Access
```
HR Team → Level 2 → Only HR documents
Finance Team → Level 2 → Only Finance documents
Management → Level 3 → All documents
```

### Scenario 2: Hierarchical Access
```
Interns → Level 1 → Single training document
Staff → Level 2 → Department-specific documents
Managers → Level 3 → All documents
IT Admin → Admin → Full system control
```

### Scenario 3: Project-Based Access
```
Project Members → Level 2 → Project-specific documents
Project Leads → Level 3 → All project documents
Contractors → Level 1 → Single specification document
```

## API Quick Reference

### Get User's Accessible Documents
```bash
GET /api/users/{user_id}/accessible-documents
```

### Assign Access Level
```bash
POST /api/admin/users/{user_id}/access-level
Body: {"user_id": "...", "access_level": 2}
```

### Assign Specific Documents (Level 2)
```bash
POST /api/admin/users/{user_id}/assign-documents
Body: {"user_id": "...", "document_ids": ["doc1", "doc2"]}
```

### Get System Statistics
```bash
GET /api/admin/statistics
```

## How Access Control Works

When a user asks a question:

1. **Question Submitted** → User asks "What is X?"
2. **Documents Retrieved** → System finds relevant documents
3. **Access Filter Applied** → Only documents user can access are used
4. **Answer Generated** → Response based on filtered documents
5. **User Receives Answer** → From their accessible documents only

## File Structure

New files created:
```
access_control.py              # Core access control logic
access_control_documents.json  # Document registry
user_access_profiles.json      # User access assignments
it_admins.json                 # IT admin accounts
static/admin.html              # Admin portal interface
ACCESS_CONTROL_GUIDE.md        # Detailed documentation
test_access_control.py         # Test suite
```

## Common Tasks

### Add a New Document
1. Upload via main interface OR copy to `attachments/` folder
2. Go to admin portal → Document Management
3. Click "Sync Documents"
4. Optionally set the access level required for the document

### Give a User More Access
1. Admin portal → User Management
2. Find the user
3. Click "Set Level"
4. Choose higher level (1 → 2 → 3)

### Restrict a Document
1. Admin portal → Document Management
2. Find the document
3. Click "Change Level"
4. Set higher level requirement (1 → 2 → 3)

### Create Custom Document Set for Level 2 User
1. Assign user to Level 2
2. Click "Assign Docs"
3. Select specific documents
4. Submit

## Security Notes

**Default Admin Credentials** - Change these in production:
- Username: `admin`
- Password: `admin123`

To create a new admin:
```bash
curl -X POST http://localhost:8000/api/admin/create \
  -H "Content-Type: application/json" \
  -d '{"username": "newadmin", "password": "yourpassword"}'
```

## Troubleshooting

### "No documents in admin portal"
→ Click "Sync Documents" button

### "User can't see any documents"
→ Assign them an access level in User Management

### "Admin login not working"
→ Check default credentials: admin / admin123

### "Access control not working"
→ Make sure documents are synced AND users have access levels assigned

## Next Steps

1. ✅ Read the full [ACCESS_CONTROL_GUIDE.md](ACCESS_CONTROL_GUIDE.md) for detailed info
2. ✅ Run `python test_access_control.py` to verify everything works
3. ✅ Visit `/admin` portal and explore the interface
4. ✅ Assign access levels to your users
5. ✅ Test by logging in as different users

## Support

For detailed documentation, see [ACCESS_CONTROL_GUIDE.md](ACCESS_CONTROL_GUIDE.md)

For testing, run: `python test_access_control.py`

---

**Your document management system is now ready with 3-level access control! 🎉**
