#!/usr/bin/env python3
"""
Test script for location geocoding and distance calculation
"""
from app import app
import requests
import json

def test_geocoding():
    """Test the geocoding functionality"""
    print("🧪 Testing Location Geocoding...")
    print("=" * 50)
    
    test_locations = [
        "Hyderabad, India",
        "Mumbai, Maharashtra, India", 
        "Delhi, India",
        "Bangalore, Karnataka, India",
        "Chennai, Tamil Nadu, India"
    ]
    
    with app.app_context():
        from routes import geocode_location, calculate_distance, get_location_info
        
        for location in test_locations:
            print(f"\n📍 Testing: {location}")
            
            # Test geocoding
            coords = geocode_location(location)
            if coords:
                print(f"   ✅ Geocoded: {coords['display_name']}")
                print(f"   📍 Coordinates: {coords['lat']}, {coords['lon']}")
            else:
                print(f"   ❌ Failed to geocode: {location}")
            
            # Test location info
            location_info = get_location_info(location)
            if location_info:
                print(f"   📋 Formatted: {location_info['formatted_address']}")
            else:
                print(f"   ❌ Failed to get location info")

def test_distance_calculation():
    """Test distance calculation between locations"""
    print("\n\n🧪 Testing Distance Calculation...")
    print("=" * 50)
    
    location_pairs = [
        ("Hyderabad, India", "Mumbai, India"),
        ("Delhi, India", "Bangalore, India"),
        ("Chennai, India", "Hyderabad, India"),
        ("Mumbai, India", "Delhi, India")
    ]
    
    with app.app_context():
        from routes import calculate_distance
        
        for loc1, loc2 in location_pairs:
            print(f"\n📏 Distance: {loc1} → {loc2}")
            
            distance = calculate_distance(loc1, loc2)
            if distance:
                print(f"   ✅ Distance: {distance} km")
            else:
                print(f"   ❌ Failed to calculate distance")

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n\n🧪 Testing API Endpoints...")
    print("=" * 50)
    
    # Test geocoding API
    print("\n📍 Testing Geocoding API...")
    response = requests.post('http://localhost:5000/api/location/geocode', 
                           json={'address': 'Hyderabad, India'})
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ API Response: {data['location']['formatted_address']}")
    else:
        print(f"   ❌ API Error: {response.status_code}")
    
    # Test distance API
    print("\n📏 Testing Distance API...")
    response = requests.post('http://localhost:5000/api/location/distance',
                           json={'location1': 'Hyderabad, India', 'location2': 'Mumbai, India'})
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ API Response: {data['distance_text']}")
    else:
        print(f"   ❌ API Error: {response.status_code}")

if __name__ == '__main__':
    print("🚀 ClotSync Location Testing Suite")
    print("Testing OpenStreetMap Nominatim API integration")
    
    try:
        test_geocoding()
        test_distance_calculation()
        
        # Only test API endpoints if server is running
        try:
            test_api_endpoints()
        except requests.exceptions.ConnectionError:
            print("\n⚠️  Server not running - skipping API endpoint tests")
            print("   Start the server with 'python app.py' to test API endpoints")
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    
    print("\n✅ Location testing completed!")



