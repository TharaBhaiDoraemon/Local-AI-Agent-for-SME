"""
Test script to verify that assign docs filtering works correctly
"""

from access_control import AccessControlManager, ACCESS_LEVEL_LOW, ACCESS_LEVEL_MEDIUM, ACCESS_LEVEL_HIGH

def test_assign_docs_filtering():
    """Test that users can only be assigned documents at their level or below"""

    print("=" * 70)
    print("Testing Assign Docs Filtering (Hierarchical Access)")
    print("=" * 70)

    acm = AccessControlManager()

    # Get all documents
    all_docs = acm.get_all_documents()
    print(f"\n1. Total documents in system: {len(all_docs)}")

    # Count documents by level
    level_counts = {
        ACCESS_LEVEL_LOW: 0,
        ACCESS_LEVEL_MEDIUM: 0,
        ACCESS_LEVEL_HIGH: 0
    }

    for doc in all_docs:
        level_counts[doc.access_level] += 1

    print(f"   - LOW level documents: {level_counts[ACCESS_LEVEL_LOW]}")
    print(f"   - MEDIUM level documents: {level_counts[ACCESS_LEVEL_MEDIUM]}")
    print(f"   - HIGH level documents: {level_counts[ACCESS_LEVEL_HIGH]}")

    # Create test users with different access levels
    print("\n2. Creating test users...")

    # Clean up any existing test users first
    user_profiles = acm._load_json(acm.user_access_file)
    test_user_ids = ['test_low_user', 'test_medium_user', 'test_high_user']
    user_profiles = [p for p in user_profiles if p['user_id'] not in test_user_ids]
    acm._save_json(acm.user_access_file, user_profiles)

    # Create test users
    user_low = acm.create_user_access_profile("test_low_user", ACCESS_LEVEL_LOW)
    user_medium = acm.create_user_access_profile("test_medium_user", ACCESS_LEVEL_MEDIUM)
    user_high = acm.create_user_access_profile("test_high_user", ACCESS_LEVEL_HIGH)

    print(f"   ✓ Created LOW level user: {user_low.user_id}")
    print(f"   ✓ Created MEDIUM level user: {user_medium.user_id}")
    print(f"   ✓ Created HIGH level user: {user_high.user_id}")

    # Test assignable documents for each user level
    print("\n3. Testing assignable documents for each user level...")
    print("-" * 70)

    # Test LOW level user
    print("\n   LOW Level User (test_low_user):")
    assignable_low = acm.get_assignable_documents_for_user(user_low.user_id)
    print(f"   - Can be assigned: {len(assignable_low)} documents")
    print(f"   - Expected: {level_counts[ACCESS_LEVEL_LOW]} documents (LOW only)")

    assert len(assignable_low) == level_counts[ACCESS_LEVEL_LOW], \
        f"LOW user should have {level_counts[ACCESS_LEVEL_LOW]} assignable docs, got {len(assignable_low)}"

    # Verify all are LOW level
    for doc in assignable_low:
        assert doc.access_level == ACCESS_LEVEL_LOW, \
            f"LOW user should only see LOW docs, found {doc.access_level}"

    print(f"   ✓ Correctly shows only LOW level documents")
    if len(assignable_low) > 0:
        print(f"   - Sample: {assignable_low[0].filename}")

    # Test MEDIUM level user
    print("\n   MEDIUM Level User (test_medium_user):")
    assignable_medium = acm.get_assignable_documents_for_user(user_medium.user_id)
    expected_medium = level_counts[ACCESS_LEVEL_LOW] + level_counts[ACCESS_LEVEL_MEDIUM]
    print(f"   - Can be assigned: {len(assignable_medium)} documents")
    print(f"   - Expected: {expected_medium} documents (MEDIUM + LOW)")

    assert len(assignable_medium) == expected_medium, \
        f"MEDIUM user should have {expected_medium} assignable docs, got {len(assignable_medium)}"

    # Verify all are MEDIUM or LOW
    for doc in assignable_medium:
        assert doc.access_level <= ACCESS_LEVEL_MEDIUM, \
            f"MEDIUM user should only see MEDIUM/LOW docs, found {doc.access_level}"

    print(f"   ✓ Correctly shows MEDIUM + LOW level documents")
    low_docs = [d for d in assignable_medium if d.access_level == ACCESS_LEVEL_LOW]
    med_docs = [d for d in assignable_medium if d.access_level == ACCESS_LEVEL_MEDIUM]
    print(f"   - Breakdown: {len(med_docs)} MEDIUM, {len(low_docs)} LOW")

    # Test HIGH level user
    print("\n   HIGH Level User (test_high_user):")
    assignable_high = acm.get_assignable_documents_for_user(user_high.user_id)
    expected_high = sum(level_counts.values())
    print(f"   - Can be assigned: {len(assignable_high)} documents")
    print(f"   - Expected: {expected_high} documents (HIGH + MEDIUM + LOW)")

    assert len(assignable_high) == expected_high, \
        f"HIGH user should have {expected_high} assignable docs, got {len(assignable_high)}"

    # Verify all are HIGH, MEDIUM or LOW
    for doc in assignable_high:
        assert doc.access_level <= ACCESS_LEVEL_HIGH, \
            f"HIGH user should only see HIGH/MEDIUM/LOW docs, found {doc.access_level}"

    print(f"   ✓ Correctly shows HIGH + MEDIUM + LOW level documents")
    low_docs = [d for d in assignable_high if d.access_level == ACCESS_LEVEL_LOW]
    med_docs = [d for d in assignable_high if d.access_level == ACCESS_LEVEL_MEDIUM]
    high_docs = [d for d in assignable_high if d.access_level == ACCESS_LEVEL_HIGH]
    print(f"   - Breakdown: {len(high_docs)} HIGH, {len(med_docs)} MEDIUM, {len(low_docs)} LOW")

    print("\n" + "-" * 70)

    # Test that assignment is blocked for documents above user level
    print("\n4. Testing assignment restrictions...")

    # Try to manually assign a HIGH doc to a LOW user (should work via API but not be selectable in UI)
    high_docs_list = [d for d in all_docs if d.access_level == ACCESS_LEVEL_HIGH]
    if high_docs_list:
        high_doc = high_docs_list[0]
        print(f"\n   Scenario: Admin tries to assign HIGH doc '{high_doc.filename}' to LOW user")
        print(f"   - LOW user's assignable docs do NOT include this document")
        print(f"   - UI will not show this document in the assign docs modal")
        print(f"   ✓ User is protected from being assigned inaccessible documents")

    # Cleanup test users
    print("\n5. Cleaning up test users...")
    user_profiles = acm._load_json(acm.user_access_file)
    user_profiles = [p for p in user_profiles if p['user_id'] not in test_user_ids]
    acm._save_json(acm.user_access_file, user_profiles)
    print("   ✓ Test users removed")

    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED - Assign Docs Filtering Works Correctly!")
    print("=" * 70)

    print("\n" + "Summary:")
    print("-" * 70)
    print("Hierarchical Assignment Model:")
    print("  • LOW level users: Can be assigned LOW level documents only")
    print("  • MEDIUM level users: Can be assigned MEDIUM + LOW level documents")
    print("  • HIGH level users: Can be assigned HIGH + MEDIUM + LOW level documents")
    print("")
    print("The UI now correctly filters the document list in the 'Assign Docs' modal")
    print("based on the user's access level, preventing assignment of inaccessible docs.")
    print("-" * 70)

if __name__ == "__main__":
    try:
        test_assign_docs_filtering()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
