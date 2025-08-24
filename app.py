from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

app = Flask(__name__)

# Secrets & DB from environment (fallback to defaults for dev)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    "mysql+pymysql://root:Sruthi.1%40@localhost/clotsync"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from extensions import db, login_manager
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login_donor'  # Set default login view

# Import models and routes after db is initialized
from models import Hospital, Patient, Donor
from routes import *

@login_manager.user_loader
def load_user(user_id):
    try:
        # Parse user type and ID from the composite ID
        if user_id.startswith('hospital_'):
            user_id_num = int(user_id.split('_')[1])
            hospital = db.session.get(Hospital, user_id_num)
            if hospital:
                return hospital
        elif user_id.startswith('donor_'):
            user_id_num = int(user_id.split('_')[1])
            donor = db.session.get(Donor, user_id_num)
            if donor:
                return donor
        elif user_id.startswith('patient_'):
            user_id_num = int(user_id.split('_')[1])
            patient = db.session.get(Patient, user_id_num)
            if patient:
                return patient
        else:
            # Fallback for backward compatibility - try to find user by ID
            hospital = db.session.get(Hospital, int(user_id))
            if hospital:
                return hospital
            patient = db.session.get(Patient, int(user_id))
            if patient:
                return patient
            donor = db.session.get(Donor, int(user_id))
            if donor:
                return donor
        
        return None
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
        return None

@login_manager.unauthorized_handler
def handle_unauthorized():
    # Dynamic redirect based on path
    path = request.path or ''
    try:
        if path.startswith('/hospital') or path in ['/update_inventory', '/transfer_blood'] or path.startswith('/get_inventory'):
            return redirect(url_for('login_hospital'))
        if path.startswith('/donor') or path.startswith('/api/donor'):
            return redirect(url_for('login_donor'))
        if path.startswith('/patient') or path.startswith('/api/patient'):
            return redirect(url_for('login_patient'))
        # Default: send to home or patient portal
        return redirect(url_for('index'))
    except Exception:
        return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
