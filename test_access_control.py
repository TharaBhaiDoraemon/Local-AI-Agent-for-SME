"""
Test script for Access Control System
Tests all 3 levels of access and admin functionality
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_admin_login():
    """Test IT admin login"""
    print_header("TEST 1: Admin Login")

    response = requests.post(
        f"{API_BASE}/admin/login",
        json={"username": "admin", "password": "admin123"}
    )

    if response.status_code == 200:
        print("✓ Admin login successful")
        print(f"  Response: {response.json()}")
        return True
    else:
        print("✗ Admin login failed")
        print(f"  Error: {response.json()}")
        return False

def test_sync_documents():
    """Test document synchronization"""
    print_header("TEST 2: Sync Documents")

    response = requests.post(f"{API_BASE}/admin/documents/sync")

    if response.status_code == 200:
        data = response.json()
        print("✓ Document sync successful")
        print(f"  Total documents: {data['total_documents']}")
        return True
    else:
        print("✗ Document sync failed")
        return False

def test_get_all_documents():
    """Test getting all documents"""
    print_header("TEST 3: Get All Documents")

    response = requests.get(f"{API_BASE}/admin/documents")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {len(data['documents'])} documents")
        for doc in data['documents'][:3]:  # Show first 3
            print(f"  - {doc['filename']} (Level {doc['access_level']})")
        return data['documents']
    else:
        print("✗ Failed to get documents")
        return []

def test_get_users():
    """Test getting all users"""
    print_header("TEST 4: Get All Users")

    response = requests.get(f"{API_BASE}/admin/users")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {len(data['users'])} users")
        for user in data['users']:
            level = user['access_level'] or 'None'
            print(f"  - {user['username']}: Level {level}, {user['accessible_documents_count']} docs")
        return data['users']
    else:
        print("✗ Failed to get users")
        return []

def test_assign_access_levels(users):
    """Test assigning different access levels"""
    print_header("TEST 5: Assign Access Levels")

    if len(users) < 3:
        print("✗ Need at least 3 users for this test")
        return False

    # Assign Level 1 to first user
    user1 = users[0]
    response = requests.post(
        f"{API_BASE}/admin/users/{user1['user_id']}/access-level",
        json={"user_id": user1['user_id'], "access_level": 1}
    )
    if response.status_code == 200:
        print(f"✓ Assigned Level 1 to {user1['username']}")
    else:
        print(f"✗ Failed to assign Level 1 to {user1['username']}")

    # Assign Level 2 to second user
    if len(users) > 1:
        user2 = users[1]
        response = requests.post(
            f"{API_BASE}/admin/users/{user2['user_id']}/access-level",
            json={"user_id": user2['user_id'], "access_level": 2}
        )
        if response.status_code == 200:
            print(f"✓ Assigned Level 2 to {user2['username']}")
        else:
            print(f"✗ Failed to assign Level 2 to {user2['username']}")

    # Assign Level 3 to third user
    if len(users) > 2:
        user3 = users[2]
        response = requests.post(
            f"{API_BASE}/admin/users/{user3['user_id']}/access-level",
            json={"user_id": user3['user_id'], "access_level": 3}
        )
        if response.status_code == 200:
            print(f"✓ Assigned Level 3 to {user3['username']}")
        else:
            print(f"✗ Failed to assign Level 3 to {user3['username']}")

    return True

def test_user_accessible_documents(users):
    """Test that users see different documents based on their level"""
    print_header("TEST 6: Verify User Document Access")

    for user in users[:3]:  # Test first 3 users
        response = requests.get(f"{API_BASE}/users/{user['user_id']}/accessible-documents")

        if response.status_code == 200:
            data = response.json()
            level = user.get('access_level', 'None')
            print(f"✓ {user['username']} (Level {level}): {len(data['documents'])} accessible documents")
        else:
            print(f"✗ Failed to get accessible documents for {user['username']}")

def test_access_info(users):
    """Test getting access info for users"""
    print_header("TEST 7: Get User Access Info")

    for user in users[:3]:
        response = requests.get(f"{API_BASE}/users/{user['user_id']}/access-info")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ {user['username']}")
            print(f"  Level: {data.get('access_level_name', 'Unknown')}")
            print(f"  Documents: {data.get('document_count', 0)}")
        else:
            print(f"✗ Failed to get access info for {user['username']}")

def test_statistics():
    """Test getting system statistics"""
    print_header("TEST 8: System Statistics")

    response = requests.get(f"{API_BASE}/admin/statistics")

    if response.status_code == 200:
        stats = response.json()
        print("✓ Statistics retrieved successfully")
        print(f"  Total Documents: {stats['total_documents']}")
        print(f"  Total Users: {stats['total_users']}")
        print(f"  Level 1 Users: {stats['users_by_level']['level_1']}")
        print(f"  Level 2 Users: {stats['users_by_level']['level_2']}")
        print(f"  Level 3 Users: {stats['users_by_level']['level_3']}")
        return True
    else:
        print("✗ Failed to get statistics")
        return False

def test_assign_specific_documents(users, documents):
    """Test assigning specific documents to a Level 2 user"""
    print_header("TEST 9: Assign Specific Documents")

    if len(users) < 2 or len(documents) < 2:
        print("✗ Need at least 2 users and 2 documents for this test")
        return False

    # Get a Level 2 user
    level2_user = None
    for user in users:
        if user.get('access_level') == 2:
            level2_user = user
            break

    if not level2_user:
        print("✗ No Level 2 user found. Assigning Level 2 to second user...")
        level2_user = users[1]
        requests.post(
            f"{API_BASE}/admin/users/{level2_user['user_id']}/access-level",
            json={"user_id": level2_user['user_id'], "access_level": 2}
        )

    # Assign first 2 documents
    doc_ids = [doc['id'] for doc in documents[:2]]

    response = requests.post(
        f"{API_BASE}/admin/users/{level2_user['user_id']}/assign-documents",
        json={"user_id": level2_user['user_id'], "document_ids": doc_ids}
    )

    if response.status_code == 200:
        print(f"✓ Assigned {len(doc_ids)} specific documents to {level2_user['username']}")
        print(f"  Documents: {[doc['filename'] for doc in documents[:2]]}")
        return True
    else:
        print(f"✗ Failed to assign specific documents")
        return False

def run_all_tests():
    """Run all access control tests"""
    print("\n" + "="*60)
    print("  ACCESS CONTROL SYSTEM TEST SUITE")
    print("="*60)
    print("\nMake sure the server is running at http://localhost:8000")
    print("Press Enter to continue...")
    input()

    try:
        # Test 1: Admin Login
        if not test_admin_login():
            print("\n❌ Admin login failed. Cannot continue tests.")
            return

        # Test 2: Sync Documents
        test_sync_documents()

        # Test 3: Get All Documents
        documents = test_get_all_documents()

        # Test 4: Get All Users
        users = test_get_users()

        if not users:
            print("\n❌ No users found. Please create some user profiles first.")
            return

        # Test 5: Assign Access Levels
        test_assign_access_levels(users)

        # Refresh user data after assignments
        users = test_get_users()

        # Test 6: Verify Document Access
        test_user_accessible_documents(users)

        # Test 7: Get Access Info
        test_access_info(users)

        # Test 8: Statistics
        test_statistics()

        # Test 9: Assign Specific Documents
        if documents:
            test_assign_specific_documents(users, documents)

        print_header("TEST SUMMARY")
        print("✓ All tests completed!")
        print("\nYou can now:")
        print("1. Visit http://localhost:8000/admin to use the admin portal")
        print("2. Login with username: admin, password: admin123")
        print("3. Manage users and documents through the web interface")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server at http://localhost:8000")
        print("Please make sure the server is running with: python app.py")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    run_all_tests()
