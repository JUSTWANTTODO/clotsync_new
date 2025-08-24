from flask import Flask, redirect, url_for, request
from urllib.parse import quote_plus
from extensions import db, login_manager

app = Flask(__name__)
app.secret_key = "supersecretkey"

db_password = quote_plus("!SKT34ye4kWd?mp")
MYSQL_URL = f"mysql+pymysql://freedb_shiva:{db_password}@sql.freedb.tech/freedb_clotsync"
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login_donor'

from models import Hospital, Patient, Donor
from routes import *

@login_manager.user_loader
def load_user(user_id):
    try:
        if user_id.startswith('hospital_'):
            user_id_num = int(user_id.split('_')[1])
            return Hospital.query.get(user_id_num)
        elif user_id.startswith('donor_'):
            user_id_num = int(user_id.split('_')[1])
            return Donor.query.get(user_id_num)
        elif user_id.startswith('patient_'):
            user_id_num = int(user_id.split('_')[1])
            return Patient.query.get(user_id_num)
        else:
            for model in [Hospital, Patient, Donor]:
                user = model.query.get(int(user_id))
                if user:
                    return user
        return None
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
        return None

@login_manager.unauthorized_handler
def handle_unauthorized():
    path = request.path or ''
    try:
        if path.startswith('/hospital') or path in ['/update_inventory', '/transfer_blood'] or path.startswith('/get_inventory'):
            return redirect(url_for('login_hospital'))
        elif path.startswith('/donor') or path.startswith('/api/donor'):
            return redirect(url_for('login_donor'))
        elif path.startswith('/patient') or path.startswith('/api/patient'):
            return redirect(url_for('login_patient'))
        return redirect(url_for('index'))
    except Exception as e:
        print("Unauthorized redirect error:", e)
        return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Tables created successfully.")
        except Exception as e:
            print("Error connecting to MySQL:", e)
    app.run(host='0.0.0.0', port=5000, debug=True)
