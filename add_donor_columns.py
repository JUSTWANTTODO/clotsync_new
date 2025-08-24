#!/usr/bin/env python3
"""
Migration Script to Add New Columns to Donors Table
Adds: latitude, longitude, gender, last_donated, next_eligible, role
"""

from app import app, db
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
        print("Starting donor table migration...")
        
        try:
            # Add new columns if they don't exist
            new_columns = [
                ('latitude', 'FLOAT NULL'),
                ('longitude', 'FLOAT NULL'),
                ('gender', 'VARCHAR(10) NULL'),
                ('last_donated', 'DATE NULL'),
                ('next_eligible', 'DATE NULL'),
                ('role', 'VARCHAR(20) DEFAULT "volunteer"')
            ]
            
            for column_name, column_def in new_columns:
                if not column_exists('donors', column_name):
                    print(f"Adding {column_name} column to donors table...")
                    db.session.execute(text(f"ALTER TABLE donors ADD COLUMN {column_name} {column_def}"))
                else:
                    print(f"Column {column_name} already exists in donors table")
            
            # Update existing records to have default role
            print("Updating existing records with default role...")
            db.session.execute(text("UPDATE donors SET role = 'volunteer' WHERE role IS NULL"))
            
            # Commit changes
            db.session.commit()
            print("Migration completed successfully!")
            
            # Verify the changes
            print("\nVerifying migration...")
            result = db.session.execute(text("DESCRIBE donors"))
            columns = result.fetchall()
            print("Current donor table columns:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
                
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    run_migration()
