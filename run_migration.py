#!/usr/bin/env python3
"""
Database Migration Script for ClotSync
This script adds user_type columns to distinguish between different user types
"""

from app import app, db
from models import Hospital, Donor, Patient
from sqlalchemy import text

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        result = db.session.execute(text(f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'"))
        return result.fetchone() is not None
    except:
        return False

def run_migration():
    with app.app_context():
        print("Starting database migration...")
        
        try:
            # Add user_type columns if they don't exist
            print("Adding user_type columns...")
            
            # Check and add columns for hospitals
            if not column_exists('hospitals', 'user_type'):
                print("Adding user_type column to hospitals table...")
                db.session.execute(text("ALTER TABLE hospitals ADD COLUMN user_type VARCHAR(20) DEFAULT 'hospital'"))
            else:
                print("user_type column already exists in hospitals table")
            
            # Check and add columns for donors
            if not column_exists('donors', 'user_type'):
                print("Adding user_type column to donors table...")
                db.session.execute(text("ALTER TABLE donors ADD COLUMN user_type VARCHAR(20) DEFAULT 'donor'"))
            else:
                print("user_type column already exists in donors table")
            
            # Check and add columns for patients
            if not column_exists('patients', 'user_type'):
                print("Adding user_type column to patients table...")
                db.session.execute(text("ALTER TABLE patients ADD COLUMN user_type VARCHAR(20) DEFAULT 'patient'"))
            else:
                print("user_type column already exists in patients table")
            
            # Update existing records
            print("Updating existing records...")
            db.session.execute(text("UPDATE hospitals SET user_type = 'hospital' WHERE user_type IS NULL"))
            db.session.execute(text("UPDATE donors SET user_type = 'donor' WHERE user_type IS NULL"))
            db.session.execute(text("UPDATE patients SET user_type = 'patient' WHERE user_type IS NULL"))
            
            # Commit changes
            db.session.commit()
            print("Migration completed successfully!")
            
            # Verify the changes
            print("\nVerifying migration...")
            hospitals = Hospital.query.all()
            donors = Donor.query.all()
            patients = Patient.query.all()
            
            print(f"Hospitals: {len(hospitals)}")
            for h in hospitals:
                print(f"  - {h.name} (ID: {h.id}, Type: {h.user_type})")
            
            print(f"Donors: {len(donors)}")
            for d in donors:
                print(f"  - {d.name} (ID: {d.id}, Type: {d.user_type})")
            
            print(f"Patients: {len(patients)}")
            for p in patients:
                print(f"  - {p.name} (ID: {p.id}, Type: {p.user_type})")
                
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    run_migration()
