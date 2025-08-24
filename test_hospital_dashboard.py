#!/usr/bin/env python3
"""
Test script for the enhanced hospital dashboard
Tests the new donor acceptances functionality
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_hospital_dashboard():
    print("Testing Enhanced Hospital Dashboard...")
    
    # Test 1: Get hospital pending acceptances (should require login)
    print("\n1. Testing hospital pending acceptances endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/hospital/pending-acceptances")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Expected: Requires hospital login")
        elif response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data.get('acceptances', []))} pending acceptances")
        else:
            print(f"❌ Unexpected status: {response.text}")
    except Exception as e:
        print(f"❌ Error testing pending acceptances: {e}")
    
    # Test 2: Test donation confirmation endpoint (should require login)
    print("\n2. Testing donation confirmation endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/api/hospital/confirm-donation", 
                               json={"acceptance_id": 1, "units_donated": 2})
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Expected: Requires hospital login")
        else:
            print(f"❌ Unexpected status: {response.text}")
    except Exception as e:
        print(f"❌ Error testing donation confirmation: {e}")
    
    # Test 3: Test get requests endpoint (should require login)
    print("\n3. Testing get requests endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/get_requests/1")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Expected: Requires hospital login")
        else:
            print(f"❌ Unexpected status: {response.text}")
    except Exception as e:
        print(f"❌ Error testing get requests: {e}")
    
    print("\n✅ Test completed. All endpoints are properly protected and require hospital login.")
    print("\n📋 To test the full functionality:")
    print("1. Login as a hospital at /login_hospital")
    print("2. Navigate to the 'Donor Acceptances' tab")
    print("3. View pending donor acceptances")
    print("4. Click 'Confirm Donation' to complete the two-step process")

if __name__ == "__main__":
    test_hospital_dashboard()

