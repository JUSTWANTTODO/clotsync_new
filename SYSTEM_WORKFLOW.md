# ClotSync Blood Donation System - Complete Workflow Guide

## 🩸 System Overview

ClotSync is a full-stack blood donation and hospital inventory management system that connects patients, donors, and hospitals to facilitate blood donations and manage blood inventory efficiently.

## 📊 Current System Status

Based on the database check, here's what's currently in the system:

### Registered Users:
- **6 Donors**: John Smith (A+), Sarah Johnson (O-), Mike Wilson (B+), Emily Davis (AB+), David Brown (O+), Karthik (A+)
- **3 Patients**: Alice Cooper (A+), Bob Miller (O-), Raju (A+)
- **3 Hospitals**: City General Hospital, Metro Medical Center, Yashoda

### Active Blood Request:
- **Patient**: Raju (A+ blood group)
- **Request**: 2 units of A+ blood (urgent)
- **Status**: Pending
- **Alerts Sent**: 2 donors (John Smith and Karthik) have been notified

## 🔄 Complete Workflow

### 1. Patient Blood Request Process

**Step 1: Patient Registration**
- Patient registers with name, blood group, location, contact, username, password
- Patient can then log in to their dashboard

**Step 2: Blood Request**
- Patient logs in and submits a blood request
- System automatically:
  - Creates a `BloodRequest` record
  - Sends alerts to all matching donors (same blood group + available)
  - Creates `DonorAlert` records for each matching donor

**Step 3: Request Fulfillment**
- Donors receive alerts and can mark donations
- Hospitals can see requests and fulfill them if they have stock
- System updates donor donation counts and request status

### 2. Donor Management Process

**Step 1: Donor Registration**
- Donor registers with name, blood group, location, contact, availability
- Donor appears in the leaderboard

**Step 2: Enhanced Alert System**
- Donors receive detailed alerts for all matching blood requests
- Each alert shows:
  - Request Code, Blood Group, Units Needed
  - Urgency level (with color-coded badges)
  - Required By date, Hospital name and location
  - Created timestamp
- Alerts are displayed in a clear, organized format

**Step 3: Two-Step Donation Process**
- **Step 1: Donor Acceptance**: Donor accepts request with optional note
- **Step 2: Hospital Confirmation**: Hospital confirms actual donation and units
- Only after hospital confirmation is the donation counted and donor's total updated

**Step 4: Partial Donation Support**
- Donors can donate fewer units than requested
- System automatically updates remaining units needed
- New alerts sent to other donors for remaining units
- Hospital inventory updated with donated units

**Step 5: Donation Tracking**
- Each confirmed donation increases the donor's donation count
- Donor can toggle availability status
- Leaderboard updates automatically

### 3. Hospital Management Process

**Step 1: Hospital Registration**
- Hospital registers with name, location, username, password
- System initializes inventory with all blood groups (0 units)

**Step 2: Inventory Management**
- Hospitals can update their blood inventory
- View current stock levels
- Transfer blood to other hospitals

**Step 3: Blood Request Management**
- Hospitals can see all pending blood requests
- Requests are sorted by urgency and distance
- Hospitals can fulfill requests if they have sufficient stock
- **NEW**: View detailed request information with patient location and distance

**Step 4: Donor Acceptance Management (NEW)**
- **Donor Acceptances Tab**: View all pending donor acceptances
- **Two-Step Process**: Confirm actual donations and specify units donated
- **Partial Donations**: Support for donors donating fewer units than requested
- **Automatic Updates**: System updates inventory, donor counts, and remaining units
- **Smart Alerts**: New alerts sent to other donors for remaining units

## 🎯 How to Use the System

### For Patients:

1. **Register/Login**: Go to `/register_patient` or `/login_patient`
2. **Submit Request**: Use the "Blood Now" feature in patient dashboard
3. **Track Status**: Monitor request status in dashboard

### For Donors:

1. **Register**: Go to `/register_donor` or visit donor portal
2. **View Alerts**: Access `/donor_dashboard` to see blood request alerts
3. **Mark Donations**: Click "Mark Donation" on alerts to complete donations
4. **Check Leaderboard**: View `/leaderboard` to see top donors

### For Hospitals:

1. **Register/Login**: Go to `/register_hospital` or `/login_hospital`
2. **Manage Inventory**: Update blood stock levels
3. **View Blood Requests**: Check the "Blood Requests" tab in dashboard
   - See all pending requests with patient details, urgency, and distance
   - Fulfill requests if you have sufficient stock
4. **Manage Donor Acceptances (NEW)**: Check the "Donor Acceptances" tab
   - View all donors who accepted blood requests
   - Confirm actual donations and specify units donated
   - Support partial donations (donor gives fewer units than requested)
   - System automatically updates inventory and donor counts

## 🔍 Current Request Status

**Patient Raju's A+ Blood Request (2 units):**

✅ **Request Created**: Successfully submitted

## 🆕 New Enhanced Donation System

### New API Endpoints:

**Hospital Donation Management:**
- `POST /api/hospital/confirm-donation` - Confirm donor donation and update units
- `GET /api/hospital/pending-acceptances` - View all pending donor acceptances

**Enhanced Donor Alerts:**
- `GET /api/donor/alerts` - Now returns detailed request information instead of simple messages
- Each alert includes complete request details: ID, code, blood group, units, urgency, dates, hospital info

### Database Changes:
- Added `units_donated` and `completed_at` fields to `donor_acceptances` table
- Enhanced tracking of partial donations and completion status

### Key Features:
1. **Two-Step Process**: Donor accepts → Hospital confirms → Donation counted
2. **Partial Donations**: Support for donors donating fewer units than requested
3. **Automatic Updates**: Remaining units automatically trigger new alerts
4. **Detailed Alerts**: Rich information display with badges and organized layout
5. **Hospital Control**: Hospitals manage final donation confirmation and unit counting
✅ **Alerts Sent**: 2 donors notified (John Smith, Karthik)
✅ **Hospital Visibility**: All hospitals can see the request
⏳ **Status**: Pending fulfillment

**Available Fulfillment Options:**
1. **Donor Donation**: John Smith or Karthik can mark donation
2. **Hospital Fulfillment**: 
   - City General Hospital (50 A+ units available) ✅
   - Metro Medical Center (35 A+ units available) ✅
   - Yashoda (15 A+ units available) ✅

## 🚀 New Features Implemented

### 1. Donor Dashboard (`/donor_dashboard`)
- View donor profile and donation count
- See blood request alerts
- Mark donations as completed
- Toggle availability status
- Access leaderboard

### 2. Enhanced Hospital Dashboard
- Blood requests tab with real-time updates
- Location-based request sorting
- One-click request fulfillment
- Inventory integration with requests

### 3. API Endpoints
- `/api/donor/profile` - Get donor information
- `/api/donor/alerts` - Get donor alerts
- `/api/donor/mark-donation` - Mark donation as completed
- `/api/donor/toggle-availability` - Toggle donor availability
- `/fulfill_request/<id>` - Hospital fulfill blood request
- `/api/location/geocode` - Geocode address to coordinates
- `/api/location/distance` - Calculate distance between locations

### 4. Location-Based Matching
- **Real-time geocoding** using OpenStreetMap Nominatim API (free)
- **Accurate distance calculation** using Haversine formula
- **Formatted addresses** for better location display
- **Requests sorted by urgency and actual distance**
- **Hospital inventory checking** for fulfillment capability
- **Location validation** and error handling

## 🔧 Technical Implementation

### Database Tables:
- `hospitals` - Hospital information and inventory
- `donors` - Donor information and donation counts
- `patients` - Patient information
- `requests` - Blood request records
- `transfers` - Blood transfer records
- `donor_alerts` - Alert notifications for donors

### Key Features:
- **Real-time Updates**: JavaScript fetches data dynamically
- **Responsive Design**: Bootstrap-based UI
- **Session Management**: Flask-Login for authentication
- **JSON Inventory**: Flexible blood group management
- **Alert System**: Automatic donor notifications

## 🎯 Next Steps

To complete the workflow:

1. **Test Donor Dashboard**: Visit `/donor_dashboard` to see alerts
2. **Mark Donation**: Click "Mark Donation" on the A+ request alert
3. **Check Hospital Dashboard**: Login as hospital to see the request
4. **Fulfill Request**: Use hospital dashboard to fulfill the request
5. **Verify Updates**: Check that donor count and request status update

## 🔗 Quick Access Links

- **Home**: `/`
- **Donor Portal**: `/donor_portal`
- **Donor Dashboard**: `/donor_dashboard`
- **Patient Portal**: `/patient_portal`
- **Hospital Login**: `/login_hospital`
- **Leaderboard**: `/leaderboard`

The system is now fully functional with a complete blood donation workflow from patient request to fulfillment!
