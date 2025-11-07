"""
Script to clean up test documents and assign random access levels to real documents
"""

from access_control import AccessControlManager, ACCESS_LEVEL_LOW, ACCESS_LEVEL_MEDIUM, ACCESS_LEVEL_HIGH
import random

def cleanup_and_assign():
    """Remove test documents and assign random access levels to existing documents"""

    print("=" * 60)
    print("Cleaning Up Test Data and Assigning Access Levels")
    print("=" * 60)

    acm = AccessControlManager()

    # Get all documents
    all_docs = acm.get_all_documents()

    print(f"\n1. Found {len(all_docs)} documents in the system")

    # Remove test documents (those created by test script)
    test_prefixes = ['low_level_doc', 'medium_level_doc', 'high_level_doc']
    removed_count = 0

    for doc in all_docs:
        if any(doc.filename.startswith(prefix) for prefix in test_prefixes):
            print(f"   Removing test document: {doc.filename}")
            acm.delete_document(doc.id)
            removed_count += 1

    print(f"\n2. Removed {removed_count} test documents")

    # Get remaining documents
    remaining_docs = acm.get_all_documents()
    print(f"\n3. {len(remaining_docs)} documents remaining")

    if len(remaining_docs) == 0:
        print("\n   No documents to assign levels to.")
        print("=" * 60)
        return

    # Assign random access levels to remaining documents
    print("\n4. Assigning random access levels to documents...")
    print("-" * 60)

    access_levels = [ACCESS_LEVEL_LOW, ACCESS_LEVEL_MEDIUM, ACCESS_LEVEL_HIGH]
    level_names = {
        ACCESS_LEVEL_LOW: "LOW",
        ACCESS_LEVEL_MEDIUM: "MEDIUM",
        ACCESS_LEVEL_HIGH: "HIGH"
    }

    for doc in remaining_docs:
        # Assign random access level
        random_level = random.choice(access_levels)
        acm.update_document_access_level(doc.id, random_level)
        print(f"   {doc.filename:40} -> {level_names[random_level]} level")

    print("-" * 60)

    # Show summary
    updated_docs = acm.get_all_documents()
    level_counts = {
        ACCESS_LEVEL_LOW: 0,
        ACCESS_LEVEL_MEDIUM: 0,
        ACCESS_LEVEL_HIGH: 0
    }

    for doc in updated_docs:
        level_counts[doc.access_level] += 1

    print(f"\n5. Summary:")
    print(f"   Total documents: {len(updated_docs)}")
    print(f"   LOW level documents: {level_counts[ACCESS_LEVEL_LOW]}")
    print(f"   MEDIUM level documents: {level_counts[ACCESS_LEVEL_MEDIUM]}")
    print(f"   HIGH level documents: {level_counts[ACCESS_LEVEL_HIGH]}")

    print("\n" + "=" * 60)
    print("✓ Cleanup and assignment complete!")
    print("=" * 60)

    # Clean up test user profiles too
    print("\n6. Cleaning up test user profiles...")
    user_profiles = acm._load_json(acm.user_access_file)
    test_user_ids = ['user_low_001', 'user_medium_002', 'user_high_003']

    original_count = len(user_profiles)
    user_profiles = [p for p in user_profiles if p['user_id'] not in test_user_ids]
    cleaned_count = original_count - len(user_profiles)

    if cleaned_count > 0:
        acm._save_json(acm.user_access_file, user_profiles)
        print(f"   Removed {cleaned_count} test user profiles")
    else:
        print("   No test user profiles found")

    print("\n✓ All cleanup complete!")

if __name__ == "__main__":
    try:
        cleanup_and_assign()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
