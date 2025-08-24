#!/usr/bin/env python3
"""
Bulk Upload Script for Donors
Handles CSV upload with 500 rows and proper password hashing
"""

import pandas as pd
import csv
from datetime import datetime, date
from werkzeug.security import generate_password_hash
import requests
import time
from app import app, db
from models import Donor

def reverse_geocode(lat, lon):
    """Reverse geocode coordinates to get location name"""
    if lat is None or lon is None:
        return "Unknown Location"
    
    try:
        # Using Nominatim (OpenStreetMap) - free and reliable
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
        headers = {
            'User-Agent': 'ClotSync-DonorUpload/1.0'  # Required by Nominatim
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Extract location components
            address = data.get('address', {})
            
            # Try to get city/town/village name
            location_parts = []
            for key in ['city', 'town', 'village', 'suburb', 'county', 'state']:
                if key in address and address[key]:
                    location_parts.append(address[key])
                    break
            
            # If no city found, use state and country
            if not location_parts:
                if 'state' in address and address['state']:
                    location_parts.append(address['state'])
                if 'country' in address and address['country']:
                    location_parts.append(address['country'])
            
            if location_parts:
                return ", ".join(location_parts)
            else:
                return f"Lat: {lat:.4f}, Lon: {lon:.4f}"
        
        # Rate limiting - wait a bit before next request
        time.sleep(1)
        return f"Lat: {lat:.4f}, Lon: {lon:.4f}"
        
    except Exception as e:
        print(f"Reverse geocoding failed for ({lat}, {lon}): {e}")
        return f"Lat: {lat:.4f}, Lon: {lon:.4f}"

def parse_date(date_str):
    """Parse date string to date object"""
    if pd.isna(date_str) or date_str == '':
        return None
    
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except ValueError:
                continue
        return None
    except:
        return None

def parse_coordinate(coord_str):
    """Parse coordinate string to float"""
    if pd.isna(coord_str) or coord_str == '':
        return None
    
    try:
        return float(coord_str)
    except:
        return None

def show_field_mapping_summary(df):
    """Show how CSV fields map to database fields"""
    print("\n=== FIELD MAPPING SUMMARY ===")
    print("CSV Column -> Database Field -> Status")
    print("-" * 50)
    
    # Direct mappings
    direct_mappings = {
        'name': 'name',
        'blood_group': 'blood_group',
        'latitude': 'latitude', 
        'longitude': 'longitude',
        'availability': 'availability',
        'donation_count': 'donations_count',
        'Gender': 'gender',
        'last_donated': 'last_donated',
        'next_eligible': 'next_eligible',
        'role': 'role',
        'password': 'password'
    }
    
    # Check each mapping
    for csv_col, db_field in direct_mappings.items():
        if csv_col in df.columns:
            print(f"✓ {csv_col} -> {db_field}")
        else:
            print(f"✗ {csv_col} -> {db_field} (MISSING)")
    
    # Fields that will use defaults
    default_fields = {
        'location': 'Auto-generated from coordinates',
        'contact': 'Auto-generated (9999999XXXX)',
        'email': 'NULL',
        'created_at': 'Auto-generated (current timestamp)',
        'user_type': 'donor'
    }
    
    print("\nFields using defaults:")
    for field, default_value in default_fields.items():
        print(f"  {field}: {default_value}")

def bulk_upload_donors(csv_file_path):
    """Bulk upload donors from CSV file"""
    with app.app_context():
        print(f"Starting bulk upload from: {csv_file_path}")
        
        try:
            # Read CSV file with headers
            df = pd.read_csv(csv_file_path)
            print(f"Loaded {len(df)} rows from CSV")
            
            # Display column names for verification
            print(f"CSV columns: {list(df.columns)}")
            
            # Check for duplicate columns
            if 'password' in df.columns and df.columns.tolist().count('password') > 1:
                print(f"\n⚠️  WARNING: CSV contains duplicate 'password' columns. Using the first one.")
                # Keep only the first password column
                password_cols = [i for i, col in enumerate(df.columns) if col == 'password']
                if len(password_cols) > 1:
                    df = df.drop(columns=[df.columns[password_cols[-1]]])  # Drop the last duplicate
                    print(f"   Removed duplicate password column.")
            
            # Show actual column mapping
            print("\n=== ACTUAL CSV COLUMN MAPPING ===")
            for i, col in enumerate(df.columns):
                print(f"Column {i}: {col}")
            
            # Check for problematic columns
            if 'eligibility_status' in df.columns:
                print(f"\n⚠️  WARNING: CSV contains 'eligibility_status' column. This will be ignored.")
            
            # Show field mapping summary
            show_field_mapping_summary(df)
            
            # Process each row
            successful_inserts = 0
            failed_inserts = 0
            
            for index, row in df.iterrows():
                try:
                    # Extract data by column names (using the actual CSV structure)
                    name = str(row['name']).strip() if pd.notna(row['name']) and str(row['name']).strip() else ''
                    blood_group = str(row['blood_group']).strip() if pd.notna(row['blood_group']) and str(row['blood_group']).strip() else ''
                    latitude = parse_coordinate(row['latitude'])
                    longitude = parse_coordinate(row['longitude'])
                    availability = str(row['availability']).lower() == 'active' if pd.notna(row['availability']) and str(row['availability']).strip() else True
                    # Parse donation_count safely
                    try:
                        if pd.notna(row['donation_count']) and str(row['donation_count']).strip():
                            donation_count = int(row['donation_count'])
                        else:
                            donation_count = 0
                    except (ValueError, TypeError):
                        print(f"Row {index + 1}: Invalid donation_count '{row['donation_count']}', using 0")
                        donation_count = 0
                    gender = str(row['Gender']).strip() if pd.notna(row['Gender']) and str(row['Gender']).strip() else None
                    last_donated = parse_date(row['last_donated'])
                    next_eligible = parse_date(row['next_eligible'])
                    role = str(row['role']).strip() if pd.notna(row['role']) and str(row['role']).strip() else 'volunteer'
                    password = str(row['password']).strip() if pd.notna(row['password']) and str(row['password']).strip() else 'default123'
                    contact = str(row['contact']).strip() if pd.notna(row['contact']) and str(row['contact']).strip() else f"9999999{index:04d}"
                    
                    # Validate required fields
                    if not name:
                        print(f"Row {index + 1}: Skipping - name is empty")
                        failed_inserts += 1
                        continue
                         
                    if not blood_group:
                        print(f"Row {index + 1}: Skipping - blood_group is empty")
                        failed_inserts += 1
                        continue
                     
                    # Validate blood_group length
                    if len(blood_group) > 25:
                        print(f"Row {index + 1}: Skipping - blood_group '{blood_group}' is too long (max 25 chars)")
                        failed_inserts += 1
                        continue
                     
                    # Check if donor already exists (by contact number)
                    existing_donor = Donor.query.filter_by(contact=contact).first()
                    if existing_donor:
                        print(f"Row {index + 1}: Donor with contact {contact} already exists, skipping...")
                        continue
                    
                    # Auto-generate location from coordinates
                    if latitude is not None and longitude is not None:
                        location = reverse_geocode(latitude, longitude)
                        print(f"Row {index + 1}: Generated location '{location}' from coordinates ({latitude}, {longitude})")
                    else:
                        location = "Unknown Location"
                    
                    # Create new donor with proper field mapping
                    donor_data = {
                        'name': name,
                        'blood_group': blood_group,
                        'location': location,
                        'contact': contact,
                        'email': None,  # No email column in CSV
                        'password': generate_password_hash(password),
                        'availability': availability,
                        'donations_count': donation_count,
                        'latitude': latitude,
                        'longitude': longitude,
                        'gender': gender,
                        'last_donated': last_donated,
                        'next_eligible': next_eligible,
                        'role': role
                        # Note: created_at will be auto-generated, user_type will default to 'donor'
                        # Note: eligibility_status will be calculated automatically by the model
                    }
                    
                    # Debug: Show what fields are being processed
                    if index < 3:  # Only show first 3 rows for debugging
                        print(f"Row {index + 1} donor_data keys: {list(donor_data.keys())}")
                        print(f"Row {index + 1} donor_data values: {list(donor_data.values())}")
                    
                    # Ensure only expected fields are included (filter out any unexpected ones)
                    expected_fields = {
                        'name', 'blood_group', 'location', 'contact', 'email', 'password',
                        'availability', 'donations_count', 'latitude', 'longitude', 'gender',
                        'last_donated', 'next_eligible', 'role'
                    }
                    
                    # Filter donor_data to only include expected fields
                    filtered_donor_data = {k: v for k, v in donor_data.items() if k in expected_fields}
                    
                    if filtered_donor_data != donor_data:
                        print(f"Row {index + 1}: Filtered out unexpected fields: {set(donor_data.keys()) - expected_fields}")
                    
                    # Debug: Show final filtered data
                    if index < 3:
                        print(f"Row {index + 1} filtered_donor_data keys: {list(filtered_donor_data.keys())}")
                        print(f"Row {index + 1} filtered_donor_data values: {list(filtered_donor_data.values())}")
                    
                    # Create donor object
                    donor = Donor(**filtered_donor_data)
                    
                    # Debug: Check what fields the donor object actually has
                    if index < 3:
                        print(f"Row {index + 1} donor object attributes:")
                        for attr in ['name', 'blood_group', 'location', 'contact', 'email', 'password', 
                                   'availability', 'donations_count', 'latitude', 'longitude', 'gender',
                                   'last_donated', 'next_eligible', 'role', 'created_at']:
                            if hasattr(donor, attr):
                                value = getattr(donor, attr)
                                print(f"  {attr}: {value} (type: {type(value)})")
                    
                    db.session.add(donor)
                    
                    successful_inserts += 1
                    
                    # Progress indicator
                    if (index + 1) % 50 == 0:
                        print(f"Processed {index + 1}/{len(df)} rows...")
                        
                except Exception as e:
                    print(f"Row {index + 1}: Error processing row - {e}")
                    failed_inserts += 1
                    continue
            
            # Commit all changes
            print("Committing changes to database...")
            db.session.commit()
            
            print(f"\nBulk upload completed!")
            print(f"Successful inserts: {successful_inserts}")
            print(f"Failed inserts: {failed_inserts}")
            print(f"Total rows processed: {len(df)}")
            
            # Verify final count
            total_donors = Donor.query.count()
            print(f"Total donors in database: {total_donors}")
            
        except Exception as e:
            print(f"Bulk upload failed: {e}")
            db.session.rollback()
            raise

def main():
    """Main function to run bulk upload"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python bulk_upload_donors.py <csv_file_path>")
        print("Example: python bulk_upload_donors.py donors_data.csv")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    
    try:
        bulk_upload_donors(csv_file_path)
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found!")
    except Exception as e:
        print(f"Error during bulk upload: {e}")

if __name__ == '__main__':
    main()
