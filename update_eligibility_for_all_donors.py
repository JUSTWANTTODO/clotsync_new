#!/usr/bin/env python3
"""
Utility script to update eligibility status for all existing donors
Run this after adding the eligibility_status column to update existing records
"""

from app import app, db
from models import Donor
from datetime import date

def update_all_donor_eligibility():
    """Update eligibility status for all existing donors"""
    with app.app_context():
        print("Starting eligibility status update for all donors...")
        
        # Get all donors
        donors = Donor.query.all()
        print(f"Found {len(donors)} donors to update")
        
        updated_count = 0
        for donor in donors:
            try:
                # Calculate eligibility status
                donor.calculate_eligibility_status()
                updated_count += 1
                
                if updated_count % 50 == 0:
                    print(f"Processed {updated_count}/{len(donors)} donors...")
                    
            except Exception as e:
                print(f"Error updating donor {donor.id} ({donor.name}): {e}")
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\nEligibility update completed successfully!")
            print(f"Updated {updated_count} donors")
            
            # Show summary
            eligible_count = Donor.query.filter_by(eligibility_status='eligible').count()
            not_eligible_count = Donor.query.filter_by(eligibility_status='not eligible').count()
            
            print(f"\nEligibility Summary:")
            print(f"  Eligible: {eligible_count}")
            print(f"  Not Eligible: {not_eligible_count}")
            print(f"  Total: {len(donors)}")
            
        except Exception as e:
            print(f"Error committing changes: {e}")
            db.session.rollback()

if __name__ == '__main__':
    update_all_donor_eligibility()
