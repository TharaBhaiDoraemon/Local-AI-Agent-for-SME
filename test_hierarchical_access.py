"""
Test script to verify hierarchical access control implementation
"""

from access_control import AccessControlManager, ACCESS_LEVEL_LOW, ACCESS_LEVEL_MEDIUM, ACCESS_LEVEL_HIGH
import json
from pathlib import Path

def test_hierarchical_access():
    """Test that hierarchical access control works correctly"""

    print("=" * 60)
    print("Testing Hierarchical Access Control")
    print("=" * 60)

    # Initialize access control manager
    acm = AccessControlManager()

    # Create test documents with different access levels
    print("\n1. Creating test documents...")

    # Clear existing documents for clean test
    if acm.documents_file.exists():
        acm._save_json(acm.documents_file, [])

    # Create documents for each level
    doc_low_1 = acm.register_document("low_level_doc1.pdf", "./test/low1.pdf", ACCESS_LEVEL_LOW)
    doc_low_2 = acm.register_document("low_level_doc2.pdf", "./test/low2.pdf", ACCESS_LEVEL_LOW)
    doc_med_1 = acm.register_document("medium_level_doc1.pdf", "./test/med1.pdf", ACCESS_LEVEL_MEDIUM)
    doc_med_2 = acm.register_document("medium_level_doc2.pdf", "./test/med2.pdf", ACCESS_LEVEL_MEDIUM)
    doc_high_1 = acm.register_document("high_level_doc1.pdf", "./test/high1.pdf", ACCESS_LEVEL_HIGH)
    doc_high_2 = acm.register_document("high_level_doc2.pdf", "./test/high2.pdf", ACCESS_LEVEL_HIGH)

    print(f"   Created 2 LOW level documents: {doc_low_1.filename}, {doc_low_2.filename}")
    print(f"   Created 2 MEDIUM level documents: {doc_med_1.filename}, {doc_med_2.filename}")
    print(f"   Created 2 HIGH level documents: {doc_high_1.filename}, {doc_high_2.filename}")

    # Configure level configurations
    print("\n2. Configuring level default documents...")

    acm.update_level_configuration(ACCESS_LEVEL_LOW, [doc_low_1.id, doc_low_2.id])
    acm.update_level_configuration(ACCESS_LEVEL_MEDIUM, [doc_med_1.id, doc_med_2.id])
    acm.update_level_configuration(ACCESS_LEVEL_HIGH, [doc_high_1.id, doc_high_2.id])

    print("   LOW level configured with 2 documents")
    print("   MEDIUM level configured with 2 documents")
    print("   HIGH level configured with 2 documents")

    # Clear existing user profiles for clean test
    if acm.user_access_file.exists():
        acm._save_json(acm.user_access_file, [])

    # Create test users with different access levels
    print("\n3. Creating test users...")

    user_low = acm.create_user_access_profile("user_low_001", ACCESS_LEVEL_LOW)
    user_medium = acm.create_user_access_profile("user_medium_002", ACCESS_LEVEL_MEDIUM)
    user_high = acm.create_user_access_profile("user_high_003", ACCESS_LEVEL_HIGH)

    print(f"   Created LOW level user: {user_low.user_id}")
    print(f"   Created MEDIUM level user: {user_medium.user_id}")
    print(f"   Created HIGH level user: {user_high.user_id}")

    # Test hierarchical access
    print("\n4. Testing hierarchical access...")
    print("\n" + "-" * 60)

    # Test LOW level user
    print("\n   LOW Level User Test:")
    low_accessible = acm.get_user_accessible_documents(user_low.user_id)
    print(f"   - Should have access to: 2 documents (LOW only)")
    print(f"   - Actually has access to: {len(low_accessible)} documents")
    print(f"   - Documents: {[doc.filename for doc in low_accessible]}")

    assert len(low_accessible) == 2, f"LOW user should have 2 docs, but has {len(low_accessible)}"
    assert all(doc.access_level == ACCESS_LEVEL_LOW for doc in low_accessible), "LOW user should only have LOW docs"
    print("   ✓ LOW level user test PASSED")

    # Test MEDIUM level user
    print("\n   MEDIUM Level User Test:")
    med_accessible = acm.get_user_accessible_documents(user_medium.user_id)
    print(f"   - Should have access to: 4 documents (MEDIUM + LOW)")
    print(f"   - Actually has access to: {len(med_accessible)} documents")
    print(f"   - Documents: {[doc.filename for doc in med_accessible]}")

    assert len(med_accessible) == 4, f"MEDIUM user should have 4 docs, but has {len(med_accessible)}"
    med_levels = [doc.access_level for doc in med_accessible]
    assert ACCESS_LEVEL_LOW in med_levels and ACCESS_LEVEL_MEDIUM in med_levels, "MEDIUM user should have MEDIUM and LOW docs"
    assert ACCESS_LEVEL_HIGH not in med_levels, "MEDIUM user should NOT have HIGH docs"
    print("   ✓ MEDIUM level user test PASSED")

    # Test HIGH level user
    print("\n   HIGH Level User Test:")
    high_accessible = acm.get_user_accessible_documents(user_high.user_id)
    print(f"   - Should have access to: 6 documents (HIGH + MEDIUM + LOW)")
    print(f"   - Actually has access to: {len(high_accessible)} documents")
    print(f"   - Documents: {[doc.filename for doc in high_accessible]}")

    assert len(high_accessible) == 6, f"HIGH user should have 6 docs, but has {len(high_accessible)}"
    high_levels = set(doc.access_level for doc in high_accessible)
    assert high_levels == {ACCESS_LEVEL_LOW, ACCESS_LEVEL_MEDIUM, ACCESS_LEVEL_HIGH}, "HIGH user should have all level docs"
    print("   ✓ HIGH level user test PASSED")

    # Test document access checks
    print("\n5. Testing individual document access checks...")

    # LOW user trying to access HIGH doc
    can_access = acm.check_document_access(user_low.user_id, doc_high_1.id)
    print(f"   - LOW user accessing HIGH doc: {can_access} (should be False)")
    assert not can_access, "LOW user should NOT access HIGH doc"

    # MEDIUM user trying to access HIGH doc
    can_access = acm.check_document_access(user_medium.user_id, doc_high_1.id)
    print(f"   - MEDIUM user accessing HIGH doc: {can_access} (should be False)")
    assert not can_access, "MEDIUM user should NOT access HIGH doc"

    # MEDIUM user trying to access LOW doc
    can_access = acm.check_document_access(user_medium.user_id, doc_low_1.id)
    print(f"   - MEDIUM user accessing LOW doc: {can_access} (should be True)")
    assert can_access, "MEDIUM user should access LOW doc"

    # HIGH user trying to access all docs
    can_access_low = acm.check_document_access(user_high.user_id, doc_low_1.id)
    can_access_med = acm.check_document_access(user_high.user_id, doc_med_1.id)
    can_access_high = acm.check_document_access(user_high.user_id, doc_high_1.id)
    print(f"   - HIGH user accessing LOW doc: {can_access_low} (should be True)")
    print(f"   - HIGH user accessing MEDIUM doc: {can_access_med} (should be True)")
    print(f"   - HIGH user accessing HIGH doc: {can_access_high} (should be True)")
    assert can_access_low and can_access_med and can_access_high, "HIGH user should access all docs"

    print("   ✓ Document access check tests PASSED")

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - Hierarchical access control is working!")
    print("=" * 60)

    # Display summary
    print("\n" + "Summary:")
    print("-" * 60)
    print("Hierarchical Access Model:")
    print("  • LOW level (1): Can access LOW level documents only")
    print("  • MEDIUM level (2): Can access MEDIUM + LOW level documents")
    print("  • HIGH level (3): Can access HIGH + MEDIUM + LOW level documents")
    print("  • ADMIN level (99): Can access ALL documents")
    print("-" * 60)

if __name__ == "__main__":
    try:
        test_hierarchical_access()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
