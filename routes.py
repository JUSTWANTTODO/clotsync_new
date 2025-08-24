from flask import render_template, request, jsonify, redirect, url_for, flash, session, make_response
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from extensions import db
from models import Hospital, Donor, Patient, BloodRequest, BloodTransfer, DonorAlert, DonorAcceptance
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, date
import json
import time
import traceback

# Hospital Routes
@app.route('/api/hospitals')
def list_hospitals():
    hospitals = Hospital.query.order_by(Hospital.name.asc()).all()
    return jsonify({
        'hospitals': [
            {
                'id': h.id,
                'name': h.name,
                'location': h.location,
                'contact': h.contact
            } for h in hospitals
        ]
    })
@app.route('/register_hospital', methods=['GET', 'POST'])
def register_hospital():
    if request.method == 'POST':
        data = request.get_json()
        
        # Check if hospital already exists
        existing_hospital = Hospital.query.filter_by(username=data['username']).first()
        if existing_hospital:
            return jsonify({'error': 'Hospital with this username already exists'}), 400
        
        # Create new hospital
        hospital = Hospital(
            name=data['name'],
            location=data['location'],
            
            username=data['username'],
            password=generate_password_hash(data['password'])
        )
        
        # Initialize inventory with all blood groups
        initial_inventory = {
            'A Negative': 0, 'A Positive': 0, 'B Positive': 0,
            'A1 Positive': 0, 'A1B Positive': 0, 'A2 Negative': 0,
            'A2B Negative': 0, 'A2B Positive': 0, 'AB Positive': 0,
            'B Negative': 0, 'Bombay Blood Group': 0, 'O Negative': 0, 'O Positive': 0
        }
        hospital.set_inventory(initial_inventory)
        
        db.session.add(hospital)
        db.session.commit()
        
        return jsonify({'message': 'Hospital registered successfully'}), 201
    
    return render_template('register_hospital.html')

@app.route('/login_hospital', methods=['GET', 'POST'])
def login_hospital():
    if request.method == 'POST':
        data = request.get_json()
        
        hospital = Hospital.query.filter_by(username=data['username']).first()
        if hospital and check_password_hash(hospital.password, data['password']):
            login_user(hospital)
            return jsonify({'message': 'Login successful', 'redirect': '/hospital_dashboard'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login_hospital.html')

@app.route('/update_inventory', methods=['POST'])
@login_required
def update_inventory():
    if not isinstance(current_user, Hospital):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    blood_group = data['blood_group']
    units = data['units']
    
    current_user.update_blood_stock(blood_group, units)
    db.session.commit()
    
    return jsonify({
        'message': 'Inventory updated successfully',
        'inventory': current_user.get_inventory()
    }), 200

@app.route('/get_inventory/<int:hospital_id>')
def get_inventory(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    return jsonify({
        'hospital_name': hospital.name,
        'inventory': hospital.get_inventory()
    })

@app.route('/api/hospital/confirm-donation', methods=['POST'])
@login_required
def confirm_donation():
    if not isinstance(current_user, Hospital):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    acceptance_id = data.get('acceptance_id')
    units_donated = data.get('units_donated')
    
    if not acceptance_id or not units_donated:
        return jsonify({'error': 'Missing acceptance_id or units_donated'}), 400
    
    # Get the acceptance record
    acceptance = DonorAcceptance.query.get(acceptance_id)
    if not acceptance:
        return jsonify({'error': 'Acceptance record not found'}), 404
    
    # Verify this acceptance is for a request from this hospital
    if acceptance.request.hospital_id != current_user.id:
        return jsonify({'error': 'Unauthorized to confirm this donation'}), 403
    
    # Update acceptance status
    acceptance.status = 'completed'
    acceptance.units_donated = units_donated
    acceptance.completed_at = datetime.utcnow()
    
    # Update donor's donation count
    donor = acceptance.donor
    donor.donations_count += 1
    
    # Update blood request status and remaining units
    blood_request = acceptance.request
    remaining_units = blood_request.units_needed - units_donated
    
    if remaining_units <= 0:
        # All units fulfilled
        blood_request.status = 'fulfilled'
        # Update hospital inventory
        current_user.update_blood_stock(blood_request.blood_group, blood_request.units_needed)
    else:
        # Partial fulfillment - update request with remaining units
        blood_request.units_needed = remaining_units
        # Update hospital inventory with donated units
        current_user.update_blood_stock(blood_request.blood_group, units_donated)
        
        # Send new alerts to other donors for remaining units
        # Only send to eligible donors
        matching_donors = Donor.query.filter_by(
            blood_group=blood_request.blood_group,
            availability=True,
            eligibility_status='eligible'
        ).filter(Donor.id != donor.id).all()
        
        # Send heartwarming messages to non-eligible donors
        non_eligible_donors = Donor.query.filter_by(
            blood_group=blood_request.blood_group,
            availability=True,
            eligibility_status='not eligible'
        ).filter(Donor.id != donor.id).all()
        
        for other_donor in matching_donors:
            # Check if this donor already has an alert for this request
            existing_alert = DonorAlert.query.filter_by(
                donor_id=other_donor.id,
                request_id=blood_request.id
            ).first()
            
            if not existing_alert:
                alert_msg = (
                    f"Updated Hospital Request {blood_request.request_code}:\n"
                    f"Hospital: {current_user.name}\n"
                    f"Patient: {blood_request.patient.name} ({blood_request.patient.gender or ''}, {blood_request.patient.age or ''})\n"
                    f"Blood: {blood_request.blood_group} | Units Still Needed: {remaining_units}\n"
                    f"Problem: {blood_request.patient.problem or 'N/A'}\n"
                    "Location: {blood_request.patient.location} ({blood_request.patient.district or ''}, {blood_request.patient.state or ''})\n"
                    f"Required By: {blood_request.requested_date_text or 'ASAP'}\n"
                    f"Contact: {blood_request.contact_name or blood_request.patient.name} - {blood_request.contact_phone or blood_request.patient.contact}"
                )
                alert = DonorAlert(
                    donor_id=other_donor.id,
                    request_id=blood_request.id,
                    hospital_id=current_user.id,
                    message=alert_msg
                )
                db.session.add(alert)
        
        # Send heartwarming messages to non-eligible donors
        for other_donor in non_eligible_donors:
            # Check if this donor already has a heartwarming message for this request
            existing_alert = DonorAlert.query.filter_by(
                donor_id=other_donor.id,
                request_id=blood_request.id
            ).first()
            
            if not existing_alert:
                # Calculate days until eligible
                from datetime import date
                today = date.today()
                days_until_eligible = (other_donor.next_eligible - today).days if other_donor.next_eligible else 0
                
                if days_until_eligible > 0:
                    heartwarming_msg = (
                        f"💝 Heartwarming Reminder - Blood Request {blood_request.request_code}:\n\n"
                        f"Dear {other_donor.name},\n\n"
                        f"We know you're always ready to help save lives! 💪\n"
                        f"Unfortunately, you're not eligible to donate right now due to the required waiting period.\n\n"
                        f"⏰ You'll be eligible to donate again in {days_until_eligible} days (around {other_donor.next_eligible.strftime('%B %d, %Y')})\n\n"
                        f"💖 Your past donations have already saved countless lives, and we can't wait to have you back!\n"
                        f"Please take care of yourself and know that your commitment to helping others is truly inspiring.\n\n"
                        f"With gratitude,\nThe ClotSync Team ❤️"
                    )
                else:
                    heartwarming_msg = (
                        f"💝 Heartwarming Reminder - Blood Request {blood_request.request_code}:\n\n"
                        f"Dear {other_donor.name},\n\n"
                        f"We know you're always ready to help save lives! 💪\n"
                        f"Unfortunately, you're not eligible to donate right now due to the required waiting period.\n\n"
                        f"⏰ You'll be eligible to donate again soon!\n\n"
                        f"💖 Your past donations have already saved countless lives, and we can't wait to have you back!\n"
                        f"Please take care of yourself and know that your commitment to helping others is truly inspiring.\n\n"
                        f"With gratitude,\nThe ClotSync Team ❤️"
                    )
                
                alert = DonorAlert(
                    donor_id=other_donor.id,
                    request_id=blood_request.id,
                    hospital_id=current_user.id,
                    message=heartwarming_msg
                )
                db.session.add(alert)
    
    db.session.commit()
    
    return jsonify({
        'message': f'Donation confirmed. {units_donated} units recorded. Donor {donor.name} donation count updated.',
        'remaining_units': remaining_units if remaining_units > 0 else 0,
        'request_status': blood_request.status
    })

@app.route('/api/hospital/pending-acceptances')
@login_required
def get_pending_acceptances():
    if not isinstance(current_user, Hospital):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all pending acceptances for requests from this hospital
    pending_acceptances = DonorAcceptance.query.join(BloodRequest).filter(
        BloodRequest.hospital_id == current_user.id,
        DonorAcceptance.status == 'accepted'
    ).order_by(DonorAcceptance.accepted_at.desc()).all()
    
    acceptances_list = []
    for acceptance in pending_acceptances:
        request = acceptance.request
        donor = acceptance.donor
        acceptances_list.append({
            'id': acceptance.id,
            'request_code': request.request_code,
            'blood_group': request.blood_group,
            'units_needed': request.units_needed,
            'urgency': request.urgency,
            'patient_name': request.patient.name,
            'patient_gender': request.patient.gender,
            'patient_age': request.patient.age,
            'patient_problem': request.patient.problem,
            'required_by': request.requested_date_text,
            'donor_name': donor.name,
            'donor_contact': donor.contact,
            'donor_location': donor.location,
            'accepted_at': acceptance.accepted_at.isoformat(),
            'note': acceptance.note
        })
    
    return jsonify({'acceptances': acceptances_list})

# Donor Routes
@app.route('/register_donor', methods=['GET', 'POST'])
def register_donor():
    if request.method == 'POST':
        data = request.get_json()
        
        # Optional password (for login), else donor is contact-only
        hashed_pw = generate_password_hash(data['password']) if data.get('password') else None
        
        # Calculate next_eligible date based on gender
        next_eligible = None
        if data.get('gender'):
            from datetime import date, timedelta
            today = date.today()
            if data['gender'].lower() == 'male':
                # Males can donate every 3 months
                next_eligible = today + timedelta(days=90)
            elif data['gender'].lower() == 'female':
                # Females can donate every 4 months
                next_eligible = today + timedelta(days=120)
        
        donor = Donor(
            name=data['name'],
            blood_group=data['blood_group'],
            location=data['location'],
            contact=data['contact'],
            email=data.get('email'),
            password=hashed_pw,
            availability=data.get('availability', True),
            gender=data.get('gender'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            next_eligible=next_eligible
        )
        
        db.session.add(donor)
        db.session.commit()
        
        # Calculate eligibility status after commit (to ensure donor has an ID)
        donor.calculate_eligibility_status()
        db.session.commit()
        
        return jsonify({'message': 'Donor registered successfully'}), 201
    
    return render_template('donor_portal.html')

@app.route('/login_donor', methods=['GET', 'POST'])
def login_donor():
    if request.method == 'POST':
        data = request.get_json()
        
        # allow login by phone number (contact) or email
        donor = Donor.query.filter(Donor.contact == data['identifier']).first()
        
        if donor and donor.password and check_password_hash(donor.password, data['password']):
            login_user(donor)
            return jsonify({'message': 'Login successful', 'redirect': '/donor_dashboard'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('login_donor.html')

@app.route('/donor_dashboard')
@login_required
def donor_dashboard():
    # Only donors can access donor dashboard
    if isinstance(current_user, Donor):
        return render_template('donor_dashboard.html')
    else:
        return redirect(url_for('login_donor'))

@app.route('/api/donor/profile')
@login_required
def donor_profile():
    if not isinstance(current_user, Donor):
        return jsonify({'error': 'Unauthorized'}), 403
    donor = current_user
    return jsonify({
        'donor': {
            'id': donor.id,
            'name': donor.name,
            'blood_group': donor.blood_group,
            'location': donor.location,
            'contact': donor.contact,
            'email': donor.email,
            'availability': donor.availability,
            'donations_count': donor.donations_count
        }
    })

@app.route('/api/donor/alerts')
@login_required
def donor_alerts():
    if not isinstance(current_user, Donor):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all pending blood requests that match donor's blood group
    matching_requests = BloodRequest.query.filter_by(
        status='pending', 
        blood_group=current_user.blood_group
    ).order_by(BloodRequest.created_at.desc()).all()
    
    alert_list = []
    for request in matching_requests:
        # Check if donor has already accepted this request
        existing_acceptance = DonorAcceptance.query.filter_by(
            donor_id=current_user.id, 
            request_id=request.id
        ).first()
        
        if existing_acceptance:
            # Donor has already accepted, show acceptance status
            alert_list.append({
                'id': request.id,
                'request_code': request.request_code,
                'blood_group': request.blood_group,
                'units_needed': request.units_needed,
                'urgency': request.urgency,
                'required_by': request.requested_date_text,
                'hospital_name': request.hospital.name if request.hospital else 'Direct Patient Request',
                'hospital_location': request.hospital.location if request.hospital else request.patient.location,
                'created_at': request.created_at.isoformat(),
                'status': 'accepted',
                'acceptance_id': existing_acceptance.id,
                'acceptance_status': existing_acceptance.status,
                'units_donated': existing_acceptance.units_donated,
                'note': existing_acceptance.note
            })
        else:
            # New request for donor to consider
            alert_list.append({
                'id': request.id,
                'request_code': request.request_code,
                'blood_group': request.blood_group,
                'units_needed': request.units_needed,
                'urgency': request.urgency,
                'required_by': request.requested_date_text,
                'hospital_name': request.hospital.name if request.hospital else 'Direct Patient Request',
                'hospital_location': request.hospital.location if request.hospital else request.patient.location,
                'created_at': request.created_at.isoformat(),
                'status': 'new',
                'acceptance_id': None,
                'acceptance_status': None,
                'units_donated': None,
                'note': None
            })
    
    return jsonify({'alerts': alert_list})

@app.route('/api/donor/mark-donation', methods=['POST'])
@login_required
def mark_donation():
    if not isinstance(current_user, Donor):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    request_id = data.get('request_id')
    
    # Get the blood request
    blood_request = BloodRequest.query.get(request_id)
    if not blood_request:
        return jsonify({'error': 'Blood request not found'}), 404
    
    donor = current_user
    
    # Check if donor already accepted this request
    existing_acceptance = DonorAcceptance.query.filter_by(
        donor_id=donor.id, 
        request_id=request_id
    ).first()
    
    if existing_acceptance:
        return jsonify({'error': 'You have already accepted this request'}), 400
    
    # Create acceptance record (Step 1: Donor accepts)
    acceptance = DonorAcceptance(
        donor_id=donor.id, 
        request_id=blood_request.id, 
        note=data.get('note'),
        status='accepted'
    )
    db.session.add(acceptance)

    # Notify hospital
    if blood_request.hospital_id:
        hospital = Hospital.query.get(blood_request.hospital_id)
        if hospital:
            hospital_alert = DonorAlert(
                donor_id=None,
                request_id=blood_request.id,
                hospital_id=hospital.id,
                message=(
                    f"Donor {donor.name} ({donor.contact}) accepted Request {blood_request.request_code}.\n"
                    f"Blood: {blood_request.blood_group} | Units: {blood_request.units_needed}\n"
                    f"Contact: {donor.contact}"
                )
            )
            db.session.add(hospital_alert)
    
    db.session.commit()
    
    return jsonify({'message': 'Acceptance recorded. Hospital has been notified. Please wait for hospital confirmation.'})

@app.route('/api/donor/toggle-availability', methods=['POST'])
@login_required
def toggle_donor_availability():
    if not isinstance(current_user, Donor):
        return jsonify({'error': 'Unauthorized'}), 403
    current_user.availability = not current_user.availability
    db.session.commit()
    return jsonify({'message': 'Availability updated successfully', 'availability': current_user.availability})

@app.route('/api/donor/requests')
@login_required
def donor_requests():
    if not isinstance(current_user, Donor):
        return jsonify({'error': 'Unauthorized'}), 403
    donor = current_user
    # Hospital-backed pending requests that match donor blood group
    q = BloodRequest.query.filter_by(status='pending', blood_group=donor.blood_group).order_by(BloodRequest.created_at.desc()).all()
    results = []
    for r in q:
        hospital_name = r.hospital.name if r.hospital else None
        hospital_loc = r.hospital.location if r.hospital else None
        dist = calculate_distance(donor.location, hospital_loc or r.patient.location)
        results.append({
            'id': r.id,
            'request_code': getattr(r, 'request_code', None),
            'blood_group': r.blood_group,
            'units_needed': r.units_needed,
            'urgency': r.urgency,
            'required_by': getattr(r, 'requested_date_text', None),
            'hospital_name': hospital_name,
            'hospital_location': hospital_loc,
            'patient_location': r.patient.location,
            'distance_text': f"{dist} km" if dist is not None else 'N/A',
            'created_at': r.created_at.isoformat()
        })
    return jsonify({'requests': results})

@app.route('/api/donor/history')
@login_required
def donor_history():
    if not isinstance(current_user, Donor):
        return jsonify({'error': 'Unauthorized'}), 403
    accepts = DonorAcceptance.query.filter_by(donor_id=current_user.id).order_by(DonorAcceptance.accepted_at.desc()).all()
    history = []
    for a in accepts:
        req = a.request
        history.append({
            'request_code': getattr(req, 'request_code', None),
            'blood_group': req.blood_group,
            'units': req.units_needed,
            'hospital': req.hospital.name if req.hospital else None,
            'location': (req.hospital.location if req.hospital else req.patient.location),
            'accepted_at': a.accepted_at.isoformat(),
            'status': a.status,
        })
    return jsonify({'history': history})

@app.route('/donor_certificate/<int:donor_id>')
def donor_certificate(donor_id: int):
    donor = Donor.query.get_or_404(donor_id)
    html = f"""
    <html><head><title>ClotSync Certificate</title>
    <style>body{{font-family:Arial;}}.card{{max-width:700px;margin:40px auto;padding:30px;border:2px solid #28a745;border-radius:12px;}}
    .title{{font-size:28px;color:#28a745;text-align:center;font-weight:bold;}}.name{{font-size:24px;text-align:center;margin-top:10px;}}
    .meta{{text-align:center;color:#555;}}</style></head>
    <body><div class="card">
    <div class="title">Certificate of Appreciation</div>
    <div class="name">This certifies that <b>{donor.name}</b></div>
    <p class="meta">Has contributed to saving lives through blood donation.</p>
    <p class="meta">Total Donations: <b>{donor.donations_count}</b></p>
    <p class="meta">Issued by ClotSync</p>
    </div></body></html>
    """
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html'
    return resp

@app.route('/find_donor/<blood_group>')
def find_donor(blood_group):
    donors = Donor.query.filter_by(
        blood_group=blood_group,
        availability=True
    ).all()
    
    donor_list = []
    for donor in donors:
        donor_list.append({
            'id': donor.id,
            'name': donor.name,
            'location': donor.location,
            'contact': donor.contact,
            'donations_count': donor.donations_count,
            'eligibility_status': donor.eligibility_status,
            'next_eligible': donor.next_eligible.isoformat() if donor.next_eligible else None
        })
    
    return jsonify({'donors': donor_list})

@app.route('/leaderboard')
def leaderboard():
    # Get top 20 donors by donation count
    top_donors = Donor.query.order_by(Donor.donations_count.desc()).limit(20).all()
    
    leaderboard_data = []
    for donor in top_donors:
        leaderboard_data.append({
            'id': donor.id,
            'name': donor.name,
            'blood_group': donor.blood_group,
            'donations_count': donor.donations_count,
            'location': donor.location,
            'eligibility_status': donor.eligibility_status,
            'gender': donor.gender
        })
    
    return jsonify({'leaderboard': leaderboard_data})

@app.route('/api/donor/leaderboard-position')
@login_required
def donor_leaderboard_position():
    """Get current donor's position in the leaderboard"""
    if not isinstance(current_user, Donor):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all donors ordered by donation count
    all_donors = Donor.query.order_by(Donor.donations_count.desc()).all()
    
    # Find current donor's position
    current_position = None
    for i, donor in enumerate(all_donors):
        if donor.id == current_user.id:
            current_position = i + 1
            break
    
    if current_position is None:
        return jsonify({'error': 'Donor not found in leaderboard'}), 404
    
    total_donors = len(all_donors)
    
    # Determine status message
    if current_position <= 20:
        status_message = f"🎉 Congratulations! You're in the TOP 20 at position #{current_position}"
        status_class = "success"
    else:
        status_message = f"📊 You're currently at position #{current_position} out of {total_donors} donors"
        status_class = "info"
    
    return jsonify({
        'current_position': current_position,
        'total_donors': total_donors,
        'status_message': status_message,
        'status_class': status_class,
        'donations_count': current_user.donations_count,
        'is_top_20': current_position <= 20
    })

@app.route('/api/donor/leaderboard-dashboard')
@login_required
def donor_leaderboard_dashboard():
    """Get leaderboard data for donor dashboard with current donor highlighting"""
    if not isinstance(current_user, Donor):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get top 20 donors
    top_donors = Donor.query.order_by(Donor.donations_count.desc()).limit(20).all()
    
    # Get current donor's position
    all_donors = Donor.query.order_by(Donor.donations_count.desc()).all()
    current_position = None
    for i, donor in enumerate(all_donors):
        if donor.id == current_user.id:
            current_position = i + 1
            break
    
    leaderboard_data = []
    for donor in top_donors:
        is_current_donor = donor.id == current_user.id
        leaderboard_data.append({
            'id': donor.id,
            'name': donor.name,
            'blood_group': donor.blood_group,
            'donations_count': donor.donations_count,
            'location': donor.location,
            'eligibility_status': donor.eligibility_status,
            'gender': donor.gender,
            'is_current_donor': is_current_donor
        })
    
    return jsonify({
        'leaderboard': leaderboard_data,
        'current_donor_position': current_position,
        'total_donors': len(all_donors),
        'is_top_20': current_position <= 20 if current_position else False
    })

# Patient Routes
@app.route('/register_patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        data = request.get_json()
        
        patient = Patient(
            name=data['name'],
            blood_group=data['blood_group'],
            location=data['location'],
            contact=data['contact'],
            gender=data.get('gender'),
            age=data.get('age'),
            problem=data.get('problem'),
            district=data.get('district'),
            state=data.get('state'),
            hospital_id=data.get('hospital_id'),
        )
        
        db.session.add(patient)
        db.session.commit()
        
        return jsonify({'message': 'Patient registered successfully', 'patient_id': patient.id}), 201
    
    return render_template('register_patient.html')

@app.route('/login_patient', methods=['GET', 'POST'])
def login_patient():
    # Removing mandatory patient login flow per new requirement; redirect to patient form
    if request.method == 'GET':
        return redirect(url_for('patient_portal'))
    return jsonify({'message': 'Patient login disabled. Use patient portal form.'})

@app.route('/request_blood', methods=['POST'])
def request_blood():
    # No login required. Expects patient_id and request details
    data = request.get_json()
    patient_id = data.get('patient_id')
    patient = Patient.query.get(patient_id) if patient_id else None
    if not patient:
        return jsonify({'error': 'Patient not found'}), 400
    
    import random, string
    request_code = 'PT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    blood_request = BloodRequest(
        patient_id=patient.id,
        hospital_id=patient.hospital_id,
        blood_group=data['blood_group'],
        urgency=data.get('urgency', 'urgent'),
        units_needed=data.get('units_needed', 1),
        request_code=request_code,
        patient_gender=patient.gender,
        patient_age=patient.age,
        patient_problem=patient.problem,
        contact_name=data.get('contact_name'),
        contact_phone=data.get('contact_phone'),
        district=patient.district,
        state=patient.state,
        requested_date_text=data.get('requested_date_text')
    )
    
    db.session.add(blood_request)
    db.session.commit()
    
    # Send alerts to matching donors and email (if provided)
    # Only send to eligible donors
    matching_donors = Donor.query.filter_by(
        blood_group=data['blood_group'],
        availability=True,
        eligibility_status='eligible'
    ).all()
    
    # Send heartwarming messages to non-eligible donors
    non_eligible_donors = Donor.query.filter_by(
        blood_group=data['blood_group'],
        availability=True,
        eligibility_status='not eligible'
    ).all()
    
    for donor in matching_donors:
        alert_msg = (
            f"Trusted Hospital Request {blood_request.request_code}:\n"
            f"Hospital: {patient.hospital.name if patient.hospital else 'N/A'}\n"
            f"Patient: {patient.name} ({patient.gender or ''}, {patient.age or ''})\n"
            f"Blood: {data['blood_group']} | Units: {data.get('units_needed',1)}\n"
            f"Problem: {patient.problem or 'N/A'}\n"
            f"Location: {patient.location} ({patient.district or ''}, {patient.state or ''})\n"
            f"Required By: {data.get('requested_date_text') or 'ASAP'}\n"
            f"Contact: {data.get('contact_name') or patient.name} - {data.get('contact_phone') or patient.contact}"
        )
        alert = DonorAlert(
            donor_id=donor.id,
            request_id=blood_request.id,
            hospital_id=patient.hospital_id,
            message=alert_msg
        )
        db.session.add(alert)
        if donor.email:
            try:
                send_email(
                    to_email=donor.email,
                    subject=f"Blood Request {blood_request.request_code}: {data['blood_group']} needed",
                    body=alert_msg
                )
            except Exception as e:
                print(f"Email send failed to {donor.email}: {e}")
    
    # Send heartwarming messages to non-eligible donors
    for donor in non_eligible_donors:
        # Check if this donor already has a heartwarming message for this request
        existing_alert = DonorAlert.query.filter_by(
            donor_id=donor.id,
            request_id=blood_request.id
        ).first()
        
        if not existing_alert:
            # Calculate days until eligible
            from datetime import date
            today = date.today()
            days_until_eligible = (donor.next_eligible - today).days if donor.next_eligible else 0
            
            if days_until_eligible > 0:
                heartwarming_msg = (
                    f"💝 Heartwarming Reminder - Blood Request {blood_request.request_code}:\n\n"
                    f"Dear {donor.name},\n\n"
                    f"We know you're always ready to help save lives! 💪\n"
                    f"Unfortunately, you're not eligible to donate right now due to the required waiting period.\n\n"
                    f"⏰ You'll be eligible to donate again in {days_until_eligible} days (around {donor.next_eligible.strftime('%B %d, %Y')})\n\n"
                    f"💖 Your past donations have already saved countless lives, and we can't wait to have you back!\n"
                    f"Please take care of yourself and know that your commitment to helping others is truly inspiring.\n\n"
                    f"With gratitude,\nThe ClotSync Team ❤️"
                )
            else:
                heartwarming_msg = (
                    f"💝 Heartwarming Reminder - Blood Request {blood_request.request_code}:\n\n"
                    f"Dear {donor.name},\n\n"
                    f"We know you're always ready to help save lives! 💪\n"
                    f"Unfortunately, you're not eligible to donate right now due to the required waiting period.\n\n"
                    f"⏰ You'll be eligible to donate again soon!\n\n"
                    f"💖 Your past donations have already saved countless lives, and we can't wait to have you back!\n"
                    f"Please take care of yourself and know that your commitment to helping others is truly inspiring.\n\n"
                    f"With gratitude,\nThe ClotSync Team ❤️"
                )
            
            alert = DonorAlert(
                donor_id=donor.id,
                request_id=blood_request.id,
                hospital_id=patient.hospital_id,
                message=heartwarming_msg
            )
            db.session.add(alert)
            
            # Send heartwarming email if available
            if donor.email:
                try:
                    send_email(
                        to_email=donor.email,
                        subject=f"💝 Heartwarming Reminder - Blood Request {blood_request.request_code}",
                        body=heartwarming_msg
                    )
                except Exception as e:
                    print(f"Heartwarming email send failed to {donor.email}: {e}")

    db.session.commit()
    
    return jsonify({
        'message': 'Blood request submitted successfully',
        'request_id': blood_request.id
    }), 201

@app.route('/patient_request_submit', methods=['POST'])
def patient_request_submit():
    """No-login patient flow: create/update patient and immediately create a blood request."""
    data = request.get_json()

    # Basic validations
    required_fields = ['name', 'blood_group', 'units_needed', 'location', 'contact']
    for f in required_fields:
        if not data.get(f):
            return jsonify({'success': False, 'error': f'Missing field: {f}'}), 400

    # Upsert patient by (name, contact) as a simple heuristic
    patient = Patient.query.filter_by(name=data['name'], contact=data['contact']).first()
    if not patient:
        patient = Patient(
            name=data['name'],
            blood_group=data['blood_group'],
            location=data.get('location'),
            contact=data.get('contact'),
            gender=data.get('gender'),
            age=data.get('age'),
            problem=data.get('problem'),
            district=data.get('district'),
            state=data.get('state'),
            hospital_id=data.get('hospital_id') or None
        )
        db.session.add(patient)
        db.session.flush()  # get patient.id
    else:
        # Update relevant fields if provided
        patient.blood_group = data.get('blood_group') or patient.blood_group
        patient.location = data.get('location') or patient.location
        patient.gender = data.get('gender') or patient.gender
        patient.age = data.get('age') or patient.age
        patient.problem = data.get('problem') or patient.problem
        patient.district = data.get('district') or patient.district
        patient.state = data.get('state') or patient.state
        if data.get('hospital_id'):
            patient.hospital_id = data.get('hospital_id')

    # Check if patient already has a request from today (within 24 hours)
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    existing_request_today = BloodRequest.query.filter(
        BloodRequest.patient_id == patient.id,
        BloodRequest.created_at >= today_start,
        BloodRequest.created_at < today_end
    ).first()
    
    if existing_request_today:
        return jsonify({
            'success': False, 
            'error': 'You have already submitted a blood request today. Please wait until tomorrow to submit another request.',
            'existing_request_code': existing_request_today.request_code,
            'existing_request_time': existing_request_today.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }), 400

    # Create blood request
    import random, string
    request_code = 'PT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    blood_request = BloodRequest(
        patient_id=patient.id,
        hospital_id=data.get('hospital_id') or patient.hospital_id,
        blood_group=data['blood_group'],
        urgency=data.get('urgency', 'urgent'),
        units_needed=int(data.get('units_needed') or 1),
        request_code=request_code,
        patient_gender=patient.gender,
        patient_age=patient.age,
        patient_problem=patient.problem,
        contact_name=data.get('contact_name') or patient.name,
        contact_phone=data.get('contact_phone') or patient.contact,
        district=patient.district,
        state=patient.state,
        requested_date_text=data.get('requested_date_text')
    )

    db.session.add(blood_request)
    db.session.commit()

    # Send alerts to matching donors
    # Only send to eligible donors
    matching_donors = Donor.query.filter_by(
        blood_group=data['blood_group'], 
        availability=True,
        eligibility_status='eligible'
    ).all()
    
    # Send heartwarming messages to non-eligible donors
    non_eligible_donors = Donor.query.filter_by(
        blood_group=data['blood_group'], 
        availability=True,
        eligibility_status='not eligible'
    ).all()
    
    for donor in matching_donors:
        alert_msg = (
            f"Trusted Hospital Request {blood_request.request_code}:\n"
            f"Hospital: {patient.hospital.name if patient.hospital else 'N/A'}\n"
            f"Patient: {patient.name} ({patient.gender or ''}, {patient.age or ''})\n"
            f"Blood: {data['blood_group']} | Units: {data.get('units_needed',1)}\n"
            f"Problem: {patient.problem or 'N/A'}\n"
            f"Location: {patient.location} ({patient.district or ''}, {patient.state or ''})\n"
            f"Required By: {data.get('requested_date_text') or 'ASAP'}\n"
            f"Contact: {data.get('contact_name') or patient.name} - {data.get('contact_phone') or patient.contact}"
        )
        alert = DonorAlert(
            donor_id=donor.id,
            request_id=blood_request.id,
            hospital_id=patient.hospital_id,
            message=alert_msg
        )
        db.session.add(alert)
        if donor.email:
            try:
                send_email(
                    to_email=donor.email,
                    subject=f"Blood Request {blood_request.request_code}: {data['blood_group']} needed",
                    body=alert_msg
                )
            except Exception as e:
                print(f"Email send failed to {donor.email}: {e}")
    
    # Send heartwarming messages to non-eligible donors
    for donor in non_eligible_donors:
        # Check if this donor already has a heartwarming message for this request
        existing_alert = DonorAlert.query.filter_by(
            donor_id=donor.id,
            request_id=blood_request.id
        ).first()
        
        if not existing_alert:
            # Calculate days until eligible
            from datetime import date
            today = date.today()
            days_until_eligible = (donor.next_eligible - today).days if donor.next_eligible else 0
            
            if days_until_eligible > 0:
                heartwarming_msg = (
                    f"💝 Heartwarming Reminder - Blood Request {blood_request.request_code}:\n\n"
                    f"Dear {donor.name},\n\n"
                    f"We know you're always ready to help save lives! 💪\n"
                    f"Unfortunately, you're not eligible to donate right now due to the required waiting period.\n\n"
                    f"⏰ You'll be eligible to donate again in {days_until_eligible} days (around {donor.next_eligible.strftime('%B %d, %Y')})\n\n"
                    f"💖 Your past donations have already saved countless lives, and we can't wait to have you back!\n"
                    f"Please take care of yourself and know that your commitment to helping others is truly inspiring.\n\n"
                    f"With gratitude,\nThe ClotSync Team ❤️"
                )
            else:
                heartwarming_msg = (
                    f"💝 Heartwarming Reminder - Blood Request {blood_request.request_code}:\n\n"
                    f"Dear {donor.name},\n\n"
                    f"We know you're always ready to help save lives! 💪\n"
                    f"Unfortunately, you're not eligible to donate right now due to the required waiting period.\n\n"
                    f"⏰ You'll be eligible to donate again soon!\n\n"
                    f"💖 Your past donations have already saved countless lives, and we can't wait to have you back!\n"
                    f"Please take care of yourself and know that your commitment to helping others is truly inspiring.\n\n"
                    f"With gratitude,\nThe ClotSync Team ❤️"
                )
            
            alert = DonorAlert(
                donor_id=donor.id,
                request_id=blood_request.id,
                hospital_id=patient.hospital_id,
                message=heartwarming_msg
            )
            db.session.add(alert)
            
            # Send heartwarming email if available
            if donor.email:
                try:
                    send_email(
                        to_email=donor.email,
                        subject=f"💝 Heartwarming Reminder - Blood Request {blood_request.request_code}",
                        body=heartwarming_msg
                    )
                except Exception as e:
                    print(f"Heartwarming email send failed to {donor.email}: {e}")

    db.session.commit()

    return jsonify({'success': True, 'request_id': blood_request.id, 'request_code': request_code}), 201


def send_email(to_email: str, subject: str, body: str):
    """Basic email sender using local SMTP relay or set env vars for SMTP creds.
    Configure environment variables if needed: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
    """
    import os
    # Read SMTP config from environment. If missing, skip sending gracefully.
    host = os.environ.get('SMTP_HOST')
    port = int(os.environ.get('SMTP_PORT', '0') or 0)
    username = os.environ.get('SMTP_USER')
    password = os.environ.get('SMTP_PASS')
    from_addr = os.environ.get('SMTP_FROM') or username or 'no-reply@clotsync.local'

    # No SMTP configuration present → do not attempt to connect
    if not host or not port:
        print('Email disabled: SMTP_HOST/SMTP_PORT not set')
        return

    # Debug: print SMTP config (remove sensitive info in production)
    print(f"Attempting email via {host}:{port} as {username}")

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_email
    msg.set_content(body)

    try:
        # Create SMTP connection
        s = smtplib.SMTP(host, port, timeout=15)
        
        # Enable debug output
        s.set_debuglevel(1)
        
        # Say hello to the server
        s.ehlo()
        
        # Start TLS encryption
        s.starttls()
        
        # Say hello again after TLS
        s.ehlo()
        
        # Login with credentials
        if username and password:
            s.login(username, password)
        
        # Send the message
        s.send_message(msg)
        
        # Close connection
        s.quit()
        
        print(f"Email sent successfully to {to_email}")
        
    except Exception as e:
        print(f"Email send failed to {to_email}: {e}")
        print(f"SMTP Error details: {type(e).__name__}: {str(e)}")
        
        # Additional debugging for common Gmail issues
        if "535" in str(e) and "Username and Password not accepted" in str(e):
            print("Gmail authentication failed. Check:")
            print("1. App Password is correct (16 characters, no spaces)")
            print("2. 2FA is enabled on Gmail account")
            print("3. 'Less secure app access' is OFF")
            print("4. App Password was generated for 'Mail' service")
        elif "Connection refused" in str(e):
            print("Connection refused. Check firewall/network settings.")
        elif "timeout" in str(e).lower():
            print("Connection timeout. Check network connectivity.")

@app.route('/api/patient/resources')
@login_required
def get_patient_resources():
    """Return available donors and hospitals for the patient's latest request."""
    if not isinstance(current_user, Patient):
        return jsonify({'error': 'Unauthorized'}), 403

    # Find the most recent pending request for this patient
    latest_request = (
        BloodRequest.query
        .filter_by(patient_id=current_user.id, status='pending')
        .order_by(BloodRequest.created_at.desc())
        .first()
    )

    if not latest_request:
        return jsonify({'request': None, 'donors': [], 'hospitals': []})

    patient_location = current_user.location
    blood_group = latest_request.blood_group
    units_needed = latest_request.units_needed

    # Matching donors (available + same blood group)
    # Prioritize eligible donors first
    eligible_donors = (
        Donor.query
        .filter_by(blood_group=blood_group, availability=True, eligibility_status='eligible')
        .all()
    )
    
    non_eligible_donors = (
        Donor.query
        .filter_by(blood_group=blood_group, availability=True, eligibility_status='not eligible')
        .all()
    )

    donors_list = []
    
    # Add eligible donors first (prioritized)
    for donor in eligible_donors:
        distance_km = calculate_distance(patient_location, donor.location)
        donors_list.append({
            'id': donor.id,
            'name': donor.name,
            'blood_group': donor.blood_group,
            'location': donor.location,
            'contact': donor.contact,
            'donations_count': donor.donations_count,
            'distance': distance_km,
            'distance_text': f"{distance_km} km" if distance_km is not None else 'N/A',
            'eligibility_status': 'eligible',
            'priority': 'high'
        })
    
    # Add non-eligible donors with lower priority
    for donor in non_eligible_donors:
        distance_km = calculate_distance(patient_location, donor.location)
        days_until_eligible = (donor.next_eligible - date.today()).days if donor.next_eligible else None
        
        donors_list.append({
            'id': donor.id,
            'name': donor.name,
            'blood_group': donor.blood_group,
            'location': donor.location,
            'contact': donor.contact,
            'donations_count': donor.donations_count,
            'distance': distance_km,
            'distance_text': f"{distance_km} km" if distance_km is not None else 'N/A',
            'eligibility_status': 'not eligible',
            'next_eligible': donor.next_eligible.isoformat() if donor.next_eligible else None,
            'days_until_eligible': days_until_eligible,
            'priority': 'low'
        })

    # Sort donors by priority first (eligible first), then by distance
    donors_list.sort(key=lambda d: (
        0 if d['priority'] == 'high' else 1,
        d['distance'] if d['distance'] is not None else float('inf')
    ))

    # Hospitals with stock for the requested blood group
    hospitals = Hospital.query.all()
    hospitals_list = []
    for hospital in hospitals:
        inv = hospital.get_inventory()
        units_available = int(inv.get(blood_group, 0)) if inv else 0
        if units_available > 0:
            distance_km = calculate_distance(patient_location, hospital.location)
            hospitals_list.append({
                'id': hospital.id,
                'name': hospital.name,
                'location': hospital.location,
                'contact': hospital.contact,
                'units_available': units_available,
                'can_fulfill': units_available >= units_needed,
                'distance': distance_km,
                'distance_text': f"{distance_km} km" if distance_km is not None else 'N/A'
            })

    hospitals_list.sort(key=lambda h: (
        0 if h['can_fulfill'] else 1,
        h['distance'] if h['distance'] is not None else float('inf')
    ))

    return jsonify({
        'request': {
            'id': latest_request.id,
            'blood_group': blood_group,
            'urgency': latest_request.urgency,
            'units_needed': units_needed,
            'created_at': latest_request.created_at.isoformat(),
            'patient_location': patient_location,
        },
        'donors': donors_list,
        'hospitals': hospitals_list
    })

@app.route('/api/patient/request-hospital', methods=['POST'])
@login_required
def request_from_hospital():
    """Send a direct request to a specific hospital"""
    if not isinstance(current_user, Patient):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    hospital_id = data.get('hospital_id')
    message = data.get('message', '')
    
    hospital = Hospital.query.get(hospital_id)
    if not hospital:
        return jsonify({'success': False, 'error': 'Hospital not found'}), 404
    
    # Create a direct request record (you might want to create a new model for this)
    # For now, we'll create a special alert/notification
    alert = DonorAlert(
        donor_id=None,  # This will be None for hospital requests
        request_id=None,  # This will be None for direct requests
        message=f"DIRECT REQUEST from Patient {current_user.name} ({current_user.contact}): {message}",
        hospital_id=hospital_id
    )
    
    db.session.add(alert)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Request sent to {hospital.name}',
        'hospital_contact': hospital.contact
    })

@app.route('/api/patient/request-donor', methods=['POST'])
@login_required
def request_from_donor():
    """Send a direct request to a specific donor"""
    if not isinstance(current_user, Patient):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    donor_id = data.get('donor_id')
    message = data.get('message', '')
    
    donor = Donor.query.get(donor_id)
    if not donor:
        return jsonify({'success': False, 'error': 'Donor not found'}), 404
    
    # Create a direct alert for the donor
    alert = DonorAlert(
        donor_id=donor_id,
        request_id=None,  # This will be None for direct requests
        message=f"DIRECT REQUEST from Patient {current_user.name} ({current_user.contact}): {message}",
        hospital_id=None
    )
    
    db.session.add(alert)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Request sent to {donor.name}',
        'donor_contact': donor.contact
    })

@app.route('/get_requests/<int:hospital_id>')
@login_required
def get_requests(hospital_id):
    if not isinstance(current_user, Hospital) or current_user.id != hospital_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all pending requests
    requests = BloodRequest.query.filter_by(status='pending').all()
    
    request_list = []
    for req in requests:
        # Check if hospital has the required blood group
        hospital_inventory = current_user.get_inventory()
        has_stock = hospital_inventory.get(req.blood_group, 0) >= req.units_needed
        
        # Calculate real distance
        distance = calculate_distance(current_user.location, req.patient.location)
        
        # Get location information
        patient_location_info = get_location_info(req.patient.location)
        hospital_location_info = get_location_info(current_user.location)
        
        request_list.append({
            'id': req.id,
            'patient_name': req.patient.name,
            'patient_location': req.patient.location,
            'patient_location_formatted': patient_location_info['formatted_address'] if patient_location_info else req.patient.location,
            'blood_group': req.blood_group,
            'urgency': req.urgency,
            'units_needed': req.units_needed,
            'created_at': req.created_at.isoformat(),
            'can_fulfill': has_stock,
            'distance': distance,
            'distance_text': f"{distance} km" if distance else "Distance unavailable",
            'hospital_location': current_user.location,
            'hospital_location_formatted': hospital_location_info['formatted_address'] if hospital_location_info else current_user.location
        })
    
    # Sort by urgency and distance (handle None distances)
    request_list.sort(key=lambda x: (
        {'emergency': 0, 'urgent': 1, 'normal': 2}[x['urgency']], 
        x['distance'] if x['distance'] is not None else float('inf')
    ))
    
    return jsonify({'requests': request_list})

import requests
import math

def geocode_location(location):
    """Geocode a location string to coordinates using Nominatim API"""
    try:
        # Use Nominatim API (free, no API key required)
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': location,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'ClotSync Blood Donation System'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
        return None
    except Exception as e:
        print(f"Geocoding error for {location}: {e}")
        return None

def calculate_distance(location1, location2):
    """Calculate distance between two locations using Haversine formula"""
    try:
        # Geocode both locations
        loc1_coords = geocode_location(location1)
        loc2_coords = geocode_location(location2)
        
        if not loc1_coords or not loc2_coords:
            return None
        
        # Haversine formula to calculate distance
        lat1, lon1 = math.radians(loc1_coords['lat']), math.radians(loc1_coords['lon'])
        lat2, lon2 = math.radians(loc2_coords['lat']), math.radians(loc2_coords['lon'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        distance = c * r
        return round(distance, 1)
    except Exception as e:
        print(f"Distance calculation error: {e}")
        return None

def get_location_info(location):
    """Get detailed location information"""
    coords = geocode_location(location)
    if coords:
        return {
            'coordinates': coords,
            'formatted_address': coords['display_name']
        }
    return None

@app.route('/fulfill_request/<int:request_id>', methods=['POST'])
@login_required
def fulfill_request(request_id):
    if not isinstance(current_user, Hospital):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    units_to_fulfill = data.get('units', 1)
    
    # Get the blood request
    blood_request = BloodRequest.query.get(request_id)
    if not blood_request:
        return jsonify({'error': 'Blood request not found'}), 404
    
    # Check if hospital has enough stock
    hospital_inventory = current_user.get_inventory()
    if hospital_inventory.get(blood_request.blood_group, 0) < units_to_fulfill:
        return jsonify({'error': 'Insufficient blood stock'}), 400
    
    # Update hospital inventory
    current_user.update_blood_stock(blood_request.blood_group, -units_to_fulfill)
    
    # Update request status
    if units_to_fulfill >= blood_request.units_needed:
        blood_request.status = 'fulfilled'
    else:
        blood_request.units_needed -= units_to_fulfill
    
    # Create transfer record (hospital to patient)
    transfer = BloodTransfer(
        from_hospital_id=current_user.id,
        to_hospital_id=None,  # Direct to patient
        blood_group=blood_request.blood_group,
        units=units_to_fulfill
    )
    
    db.session.add(transfer)
    db.session.commit()
    
    return jsonify({
        'message': 'Request fulfilled successfully',
        'inventory': current_user.get_inventory()
    })

# Transfer Routes
@app.route('/transfer_blood', methods=['POST'])
@login_required
def transfer_blood():
    if not isinstance(current_user, Hospital):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Check if source hospital has enough blood
    source_inventory = current_user.get_inventory()
    blood_group = data['blood_group']
    units = data['units']
    
    if source_inventory.get(blood_group, 0) < units:
        return jsonify({'error': 'Insufficient blood stock'}), 400
    
    # Create transfer record
    transfer = BloodTransfer(
        from_hospital_id=current_user.id,
        to_hospital_id=data['to_hospital_id'],
        blood_group=blood_group,
        units=units
    )
    
    # Update inventories
    current_user.update_blood_stock(blood_group, -units)
    
    to_hospital = Hospital.query.get(data['to_hospital_id'])
    if to_hospital:
        to_hospital.update_blood_stock(blood_group, units)
    
    db.session.add(transfer)
    db.session.commit()
    
    return jsonify({
        'message': 'Blood transfer initiated successfully',
        'transfer_id': transfer.id
    }), 201

# AI/ML Routes
@app.route('/predict_shortage')
def predict_shortage():
    # Dummy ML API - returns hardcoded predictions
    predictions = {
        "B Positive": "shortage in 2 days",
        "O Negative": "adequate",
        "A Positive": "adequate",
        "A Negative": "shortage in 5 days",
        "B Negative": "adequate",
        "AB Positive": "shortage in 1 day",
        "A2B Negative": "adequate",
        "O Positive": "shortage in 3 days"
    }
    
    return jsonify(predictions)

@app.route('/send_alert/<int:donor_id>', methods=['POST'])
def send_alert(donor_id):
    # Mock alert system
    donor = Donor.query.get_or_404(donor_id)
    
    # In a real system, this would send SMS/email
    return jsonify({
        'message': f'Alert sent to donor {donor.name}',
        'donor_id': donor_id
    })

@app.route('/api/location/geocode', methods=['POST'])
def geocode_address():
    """API endpoint to geocode an address"""
    data = request.get_json()
    address = data.get('address')
    
    if not address:
        return jsonify({'error': 'Address is required'}), 400
    
    location_info = get_location_info(address)
    
    if location_info:
        return jsonify({
            'success': True,
            'location': location_info
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Could not geocode address'
        }), 404

@app.route('/api/location/distance', methods=['POST'])
def calculate_distance_api():
    """API endpoint to calculate distance between two locations"""
    data = request.get_json()
    location1 = data.get('location1')
    location2 = data.get('location2')
    
    if not location1 or not location2:
        return jsonify({'error': 'Both locations are required'}), 400
    
    distance = calculate_distance(location1, location2)
    
    if distance is not None:
        return jsonify({
            'success': True,
            'distance_km': distance,
            'distance_text': f"{distance} km"
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Could not calculate distance'
        }), 404

# Basic Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hospital_dashboard')
@login_required
def hospital_dashboard():
    if isinstance(current_user, Hospital):
        return render_template('hospital_dashboard.html', hospital=current_user)
    return redirect(url_for('login_hospital'))

@app.route('/donor_portal')
def donor_portal():
    return render_template('donor_portal.html')

@app.route('/patient_portal')
def patient_portal():
    return render_template('patient_portal.html')

@app.route('/patient_request')
def patient_request():
    return render_template('patient_request.html')

# Dashboard Routes
@app.route('/patient_dashboard')
@login_required
def patient_dashboard():
    if isinstance(current_user, Patient):
        return render_template('patient_dashboard.html', patient=current_user)
    return redirect(url_for('login_patient'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/donor/check_eligibility/<int:donor_id>')
def check_donor_eligibility(donor_id):
    """Check eligibility status for a specific donor"""
    from datetime import date
    donor = Donor.query.get_or_404(donor_id)
    
    # Calculate current eligibility status
    donor.calculate_eligibility_status()
    db.session.commit()
    
    return jsonify({
        'donor_id': donor.id,
        'name': donor.name,
        'gender': donor.gender,
        'last_donated': donor.last_donated.isoformat() if donor.last_donated else None,
        'next_eligible': donor.next_eligible.isoformat() if donor.next_eligible else None,
        'eligibility_status': donor.eligibility_status,
        'days_since_last_donation': (date.today() - donor.last_donated).days if donor.last_donated else None
    })

@app.route('/api/donor/update_last_donation/<int:donor_id>', methods=['POST'])
def update_last_donation(donor_id):
    """Update last donation date and recalculate eligibility"""
    donor = Donor.query.get_or_404(donor_id)
    data = request.get_json()
    
    if 'last_donated' not in data:
        return jsonify({'error': 'last_donated date is required'}), 400
    
    try:
        # Parse the date string
        from datetime import datetime
        last_donated = datetime.strptime(data['last_donated'], '%Y-%m-%d').date()
        
        # Update last donation date
        donor.last_donated = last_donated
        
        # Recalculate eligibility status
        donor.calculate_eligibility_status()
        
        # Update donations count
        donor.donations_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Last donation date updated successfully',
            'eligibility_status': donor.eligibility_status,
            'next_eligible': donor.next_eligible.isoformat() if donor.next_eligible else None
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

# Chatbot API endpoint
@app.route('/patient_chat_api', methods=['POST'])
def patient_chat_api():
    """Handle chatbot messages for thalassemia and blood donation FAQs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'reply': 'Invalid request format. Please try again.'}), 400
            
        message = data.get('message', '').strip()
        history = data.get('history', '')
        
        if not message:
            return jsonify({'reply': 'Please enter a message.'}), 400
        
        # Import and use the FAQ handler
        try:
            from faq import handle_message
            reply = handle_message(message, history)
            
            if not reply:
                reply = "I'm sorry, I couldn't process your request. Please try asking something else."
                
            return jsonify({'reply': reply})
            
        except ImportError as e:
            print(f"FAQ module import error: {e}")
            return jsonify({'reply': 'Chatbot service is temporarily unavailable. Please try again later.'}), 500
        except Exception as e:
            print(f"FAQ handler error: {e}")
            return jsonify({'reply': 'I encountered an error processing your message. Please try again.'}), 500
        
    except Exception as e:
        print(f"Chatbot API error: {e}")
        return jsonify({'reply': 'Sorry, I encountered an error. Please try again.'}), 500

# Chatbot widget endpoint
@app.route('/chatbot_widget')
def chatbot_widget():
    """Serve the chatbot widget HTML"""
    return render_template('clotsync_chatbot_widget.html')

# Reports route
@app.route('/admin_reports')
def admin_reports():
    """Generate and display admin reports"""
    try:
        # Import the reports module
        from reports import generate_ai_report_from_db
        
        # Generate report from database
        report = generate_ai_report_from_db()
        
        return render_template('report.html', report=report)
        
    except Exception as e:
        print(f"Report generation error: {e}")
        return render_template('report.html', report={
            'narrative': 'Error generating report. Please try again.',
            'predictive_outlook': 'Report generation failed.',
            'personas': 'Unable to load donor personas.',
            'impact_simulation': 'Impact simulation unavailable.',
            'anomaly_risk': 'Risk detection failed.'
        })

# API endpoint for reports (for AJAX calls)
@app.route('/api/admin_reports')
def api_admin_reports():
    """API endpoint to get report data"""
    try:
        from reports import generate_ai_report_from_db
        report = generate_ai_report_from_db()
        return jsonify(report)
    except Exception as e:
        print(f"API report error: {e}")
        return jsonify({'error': 'Failed to generate report'}), 500

# Debug route for testing database data
@app.route('/debug_donors')
def debug_donors():
    """Debug route to check donor data structure"""
    try:
        from models import Donor
        donors = Donor.query.all()
        
        debug_info = []
        for i, donor in enumerate(donors[:5]):  # Show first 5 donors
            debug_info.append({
                'id': donor.id,
                'name': donor.name,
                'blood_group': donor.blood_group,
                'location': donor.location,
                'donations_count': donor.donations_count,
                'last_donated': str(donor.last_donated) if donor.last_donated else None,
                'next_eligible': str(donor.next_eligible) if donor.next_eligible else None,
                'eligibility_status': donor.eligibility_status,
                'gender': donor.gender,
                'created_at': str(donor.created_at) if donor.created_at else None,
                'last_donated_type': type(donor.last_donated).__name__ if donor.last_donated else 'None',
                'next_eligible_type': type(donor.next_eligible).__name__ if donor.next_eligible else 'None'
            })
        
        return jsonify({
            'total_donors': len(donors),
            'sample_donors': debug_info,
            'message': 'Debug data retrieved successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': str(traceback.format_exc())
        }), 500
