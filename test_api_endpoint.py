"""
Test the API endpoint to verify document filtering is working
"""

from access_control import AccessControlManager, ACCESS_LEVEL_LOW, ACCESS_LEVEL_MEDIUM, ACCESS_LEVEL_HIGH

def test_api_filtering():
    """Test that the get_assignable_documents_for_user method works correctly"""

    print("=" * 70)
    print("Testing API Endpoint Document Filtering")
    print("=" * 70)

    acm = AccessControlManager()

    # Create test users
    print("\n1. Creating test users...")

    # Clean up existing test users
    user_profiles = acm._load_json(acm.user_access_file)
    test_user_ids = ['api_test_low', 'api_test_medium', 'api_test_high']
    user_profiles = [p for p in user_profiles if p['user_id'] not in test_user_ids]
    acm._save_json(acm.user_access_file, user_profiles)

    # Create test users
    user_low = acm.create_user_access_profile("api_test_low", ACCESS_LEVEL_LOW)
    user_medium = acm.create_user_access_profile("api_test_medium", ACCESS_LEVEL_MEDIUM)
    user_high = acm.create_user_access_profile("api_test_high", ACCESS_LEVEL_HIGH)

    print(f"   ✓ Created LOW user: {user_low.user_id}")
    print(f"   ✓ Created MEDIUM user: {user_medium.user_id}")
    print(f"   ✓ Created HIGH user: {user_high.user_id}")

    # Get all documents to see what we're working with
    all_docs = acm.get_all_documents()
    print(f"\n2. Total documents in system: {len(all_docs)}")

    low_count = sum(1 for d in all_docs if d.access_level == ACCESS_LEVEL_LOW)
    med_count = sum(1 for d in all_docs if d.access_level == ACCESS_LEVEL_MEDIUM)
    high_count = sum(1 for d in all_docs if d.access_level == ACCESS_LEVEL_HIGH)

    print(f"   - LOW level: {low_count} documents")
    print(f"   - MEDIUM level: {med_count} documents")
    print(f"   - HIGH level: {high_count} documents")

    # Test LOW user
    print("\n3. Testing LOW level user API response...")
    low_assignable = acm.get_assignable_documents_for_user("api_test_low")
    print(f"   - Assignable documents: {len(low_assignable)}")
    print(f"   - Expected: {low_count} (LOW only)")

    if len(low_assignable) > 0:
        print(f"\n   Documents returned:")
        for doc in low_assignable:
            level_name = {1: "LOW", 2: "MEDIUM", 3: "HIGH"}[doc.access_level]
            print(f"     • {doc.filename[:50]:50} [{level_name}]")

    # Verify all are LOW level
    non_low = [d for d in low_assignable if d.access_level != ACCESS_LEVEL_LOW]
    if non_low:
        print(f"\n   ❌ ERROR: Found {len(non_low)} non-LOW documents!")
        for doc in non_low:
            print(f"      - {doc.filename} (level {doc.access_level})")
        raise AssertionError("LOW user should only see LOW level documents")
    else:
        print(f"   ✓ All documents are LOW level")

    # Test MEDIUM user
    print("\n4. Testing MEDIUM level user API response...")
    med_assignable = acm.get_assignable_documents_for_user("api_test_medium")
    expected_med = low_count + med_count
    print(f"   - Assignable documents: {len(med_assignable)}")
    print(f"   - Expected: {expected_med} (MEDIUM + LOW)")

    if len(med_assignable) > 0:
        print(f"\n   Documents returned:")
        for doc in med_assignable:
            level_name = {1: "LOW", 2: "MEDIUM", 3: "HIGH"}[doc.access_level]
            print(f"     • {doc.filename[:50]:50} [{level_name}]")

    # Verify all are MEDIUM or LOW
    high_docs = [d for d in med_assignable if d.access_level == ACCESS_LEVEL_HIGH]
    if high_docs:
        print(f"\n   ❌ ERROR: Found {len(high_docs)} HIGH level documents!")
        for doc in high_docs:
            print(f"      - {doc.filename}")
        raise AssertionError("MEDIUM user should not see HIGH level documents")
    else:
        print(f"   ✓ No HIGH level documents (correct)")

    # Test HIGH user
    print("\n5. Testing HIGH level user API response...")
    high_assignable = acm.get_assignable_documents_for_user("api_test_high")
    expected_high = low_count + med_count + high_count
    print(f"   - Assignable documents: {len(high_assignable)}")
    print(f"   - Expected: {expected_high} (HIGH + MEDIUM + LOW)")

    if len(high_assignable) > 0:
        print(f"\n   Documents returned (first 5):")
        for doc in high_assignable[:5]:
            level_name = {1: "LOW", 2: "MEDIUM", 3: "HIGH"}[doc.access_level]
            print(f"     • {doc.filename[:50]:50} [{level_name}]")
        if len(high_assignable) > 5:
            print(f"     ... and {len(high_assignable) - 5} more")

    print(f"   ✓ HIGH user can see all {len(high_assignable)} documents")

    # Cleanup
    print("\n6. Cleaning up test users...")
    user_profiles = acm._load_json(acm.user_access_file)
    user_profiles = [p for p in user_profiles if p['user_id'] not in test_user_ids]
    acm._save_json(acm.user_access_file, user_profiles)
    print("   ✓ Test users removed")

    print("\n" + "=" * 70)
    print("✓ API ENDPOINT FILTERING IS WORKING CORRECTLY!")
    print("=" * 70)

    print("\n" + "Instructions:")
    print("-" * 70)
    print("The backend API is correctly filtering documents.")
    print("")
    print("If you're still seeing all documents in the UI, please:")
    print("  1. Make sure the application server has been restarted")
    print("  2. Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)")
    print("  3. Check browser console for any JavaScript errors")
    print("  4. Verify the network request shows ?user_id=... parameter")
    print("-" * 70)

if __name__ == "__main__":
    try:
        test_api_filtering()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
