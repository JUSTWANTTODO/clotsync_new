from extensions import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func
import json

class Hospital(UserMixin, db.Model):
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), default='hospital')  # Add user type identifier
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(20), nullable=False)  # Add contact field
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    inventory = db.Column(db.Text, default='{}')  # JSON string
    
    def get_id(self):
        return f"hospital_{self.id}"  # Unique identifier across all user types
    
    def get_inventory(self):
        return json.loads(self.inventory)
    
    def set_inventory(self, inventory_dict):
        self.inventory = json.dumps(inventory_dict)
    
    def update_blood_stock(self, blood_group, units):
        inventory = self.get_inventory()
        inventory[blood_group] = inventory.get(blood_group, 0) + units
        self.set_inventory(inventory)

class Donor(UserMixin, db.Model):
    __tablename__ = 'donors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), default='donor')  # Add user type identifier
    name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(25), nullable=False)  # Fixed: Increased from String(3) to String(25) for "Bombay Blood Group"
    location = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(255), nullable=True)
    availability = db.Column(db.Boolean, default=True)
    donations_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=func.now())  # Fixed: Use func.now() instead of datetime.utcnow
    
    # New columns for enhanced donor data
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # Male, Female, Other
    last_donated = db.Column(db.Date, nullable=True)
    next_eligible = db.Column(db.Date, nullable=True)
    role = db.Column(db.String(20), default='volunteer')  # Emergency donor, bridge donor, volunteer, guest donor
    eligibility_status = db.Column(db.String(20), default='eligible')  # eligible, not eligible
    
    def get_id(self):
        return f"donor_{self.id}"  # Unique identifier across all user types
    
    def calculate_eligibility_status(self):
        """Calculate eligibility status based on gender and donation intervals"""
        from datetime import date
        
        if not self.gender or not self.last_donated:
            # If no gender or last donation date, default to eligible
            self.eligibility_status = 'eligible'
            return
        
        today = date.today()
        
        # Calculate required gap based on gender
        if self.gender.lower() == 'male':
            required_gap_days = 120  # 4 months for males
        elif self.gender.lower() == 'female':
            required_gap_days = 90   # 3 months for females
        else:
            # For 'Other' gender, use 4 months as default
            required_gap_days = 120
        
        # Calculate days since last donation
        days_since_last_donation = (today - self.last_donated).days
        
        # Update eligibility status
        if days_since_last_donation >= required_gap_days:
            self.eligibility_status = 'eligible'
        else:
            self.eligibility_status = 'not eligible'
        
        # Update next_eligible date if needed
        if self.eligibility_status == 'not eligible':
            from datetime import timedelta
            self.next_eligible = self.last_donated + timedelta(days=required_gap_days)

class Patient(UserMixin, db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), default='patient')  # Add user type identifier
    name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(25), nullable=False)  # Fixed: Increased from String(3) to String(25) for "Bombay Blood Group"
    location = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    problem = db.Column(db.String(255), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())  # Fixed: Use func.now() instead of datetime.utcnow
    
    hospital = db.relationship('Hospital', backref='patients')
    
    def get_id(self):
        return f"patient_{self.id}"  # Unique identifier across all user types

class BloodRequest(db.Model):
    __tablename__ = 'requests'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)
    blood_group = db.Column(db.String(25), nullable=False)  # Fixed: Increased from String(3) to String(25) for "Bombay Blood Group"
    urgency = db.Column(db.String(20), default='normal')  # normal, urgent, emergency
    status = db.Column(db.String(20), default='pending')  # pending, fulfilled, cancelled
    units_needed = db.Column(db.Integer, default=1)
    request_code = db.Column(db.String(50), nullable=True)
    patient_gender = db.Column(db.String(10), nullable=True)
    patient_age = db.Column(db.Integer, nullable=True)
    patient_problem = db.Column(db.String(255), nullable=True)
    contact_name = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    requested_date_text = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())  # Fixed: Use func.now() instead of datetime.utcnow
    
    patient = db.relationship('Patient', backref='requests')
    hospital = db.relationship('Hospital', backref='requests')

class DonorAcceptance(db.Model):
    __tablename__ = 'donor_acceptances'

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    accepted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='accepted')  # accepted, completed, cancelled
    note = db.Column(db.Text, nullable=True)
    units_donated = db.Column(db.Integer, nullable=True)  # How many units this donor actually donated
    completed_at = db.Column(db.DateTime, nullable=True)  # When hospital marked as completed

    donor = db.relationship('Donor', backref='acceptances')
    request = db.relationship('BloodRequest', backref='acceptances')

class BloodTransfer(db.Model):
    __tablename__ = 'transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    from_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    to_hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    blood_group = db.Column(db.String(3), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    
    from_hospital = db.relationship('Hospital', foreign_keys=[from_hospital_id])
    to_hospital = db.relationship('Hospital', foreign_keys=[to_hospital_id])

class DonorAlert(db.Model):
    __tablename__ = 'donor_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donors.id'), nullable=True)  # Nullable for hospital requests
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=True)  # Nullable for direct requests
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)  # For hospital requests
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    donor = db.relationship('Donor', backref='alerts')
    request = db.relationship('BloodRequest', backref='alerts')
    hospital = db.relationship('Hospital', backref='alerts')
