#!/usr/bin/env python3
"""
Test script to verify the model management API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing Model Management API Endpoints")
print("=" * 50)

try:
    # Test 1: Get available models
    print("\n1. Testing GET /api/models/available")
    response = requests.get(f"{BASE_URL}/api/models/available", timeout=5)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
    else:
        print(f"   Error: {response.text}")

    # Test 2: Get current model selection
    print("\n2. Testing GET /api/models/current")
    response = requests.get(f"{BASE_URL}/api/models/current", timeout=5)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
    else:
        print(f"   Error: {response.text}")

    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\nIf you see models listed above, the API is working correctly.")
    print("If not, make sure the server is running: python app.py")

except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Could not connect to the server")
    print("Make sure the server is running:")
    print("   python app.py")
    print("\nThen run this test script again:")
    print("   python test_api.py")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
