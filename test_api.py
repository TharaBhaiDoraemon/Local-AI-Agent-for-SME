"""
Test API endpoints to ensure they work properly with the new functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    # Test the table query endpoint
    print("Testing API endpoints...")
    
    # Test available tables endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/table/available", timeout=5)
        print(f"GET /api/table/available - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Found {data.get('count', 0)} tables")
            print(f"  Tables: {list(t['name'] for t in data.get('tables', []))}")
        else:
            print(f"  Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("  Server not running - API tests skipped")
        return
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test a table query
    try:
        query_payload = {
            "question": "compare yt_data_2023 and yt_data_2024 sum",
            "profile_id": "test",
            "chat_id": None
        }
        
        response = requests.post(f"{BASE_URL}/api/table/query", 
                                json=query_payload,
                                timeout=10)
        print(f"POST /api/table/query - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Has data: {data.get('has_data')}")
            print(f"  Download URL: {data.get('download_url')}")
        else:
            print(f"  Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("  Server not running - skipping query test")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()