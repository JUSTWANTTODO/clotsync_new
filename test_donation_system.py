#!/usr/bin/env python3
"""
Test script for the enhanced donation system
Tests the two-step donation process and partial donations
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_donation_system():
    print("Testing Enhanced Donation System...")
    
    # Test 1: Get donor alerts (should show detailed information)
    print("\n1. Testing donor alerts endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/donor/alerts")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('alerts', []))} alerts")
            if data.get('alerts'):
                alert = data['alerts'][0]
                print(f"Sample alert structure:")
                print(f"  - Request Code: {alert.get('request_code')}")
                print(f"  - Blood Group: {alert.get('blood_group')}")
                print(f"  - Units Needed: {alert.get('units_needed')}")
                print(f"  - Hospital: {alert.get('hospital_name')}")
                print(f"  - Status: {alert.get('status')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing alerts: {e}")
    
    # Test 2: Get hospital pending acceptances
    print("\n2. Testing hospital pending acceptances endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/hospital/pending-acceptances")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('acceptances', []))} pending acceptances")
        elif response.status_code == 401:
            print("Expected: Requires hospital login")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing pending acceptances: {e}")
    
    # Test 3: Test donation confirmation endpoint
    print("\n3. Testing donation confirmation endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/api/hospital/confirm-donation", 
                               json={"acceptance_id": 1, "units_donated": 2})
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("Expected: Requires hospital login")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error testing donation confirmation: {e}")
    
    print("\nTest completed. Check the responses above for expected behavior.")

if __name__ == "__main__":
    test_donation_system()

