#!/usr/bin/env python3
from app import app, db
from models import Hospital, Donor, Patient, BloodRequest, BloodTransfer, DonorAlert

def check_data():
    with app.app_context():
        print("=== CLOTSYNC DATABASE STATUS ===")
        
        # Check donors
        donors = Donor.query.all()
        print(f"\n📋 DONORS ({len(donors)}):")
        for donor in donors:
            print(f"  - {donor.name} ({donor.blood_group}) - {donor.location} - Available: {donor.availability}")
        
        # Check patients
        patients = Patient.query.all()
        print(f"\n🏥 PATIENTS ({len(patients)}):")
        for patient in patients:
            print(f"  - {patient.name} ({patient.blood_group}) - {patient.location}")
        
        # Check blood requests
        requests = BloodRequest.query.all()
        print(f"\n🩸 BLOOD REQUESTS ({len(requests)}):")
        for req in requests:
            print(f"  - ID: {req.id} | Patient: {req.patient.name} | Blood: {req.blood_group} | Units: {req.units_needed} | Status: {req.status} | Urgency: {req.urgency}")
        
        # Check donor alerts
        alerts = DonorAlert.query.all()
        print(f"\n🔔 DONOR ALERTS ({len(alerts)}):")
        for alert in alerts:
            print(f"  - Donor: {alert.donor.name} | Request ID: {alert.request_id} | Read: {alert.is_read}")
            print(f"    Message: {alert.message}")
        
        # Check hospitals
        hospitals = Hospital.query.all()
        print(f"\n🏥 HOSPITALS ({len(hospitals)}):")
        for hospital in hospitals:
            print(f"  - {hospital.name} - {hospital.location}")
            inventory = hospital.get_inventory()
            print(f"    Inventory: {inventory}")

if __name__ == '__main__':
    check_data()


