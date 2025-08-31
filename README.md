# ClotSync - Blood Donation & Hospital Inventory Management System

A comprehensive full-stack web application for managing blood donations, hospital inventory, and connecting donors with patients in need.

## 🚀 Features

### Hospital Dashboard
- **Registration & Login**: Secure authentication for hospitals
- **Inventory Management**: Real-time blood stock tracking (A+, A-, B+, B-, AB+, AB-, O+, O-)
- **Shortage Predictions**: AI-powered forecasting for blood shortages
- **Hospital Transfers**: Coordinate blood transfers between facilities
- **Request Management**: View and respond to patient blood requests

### Donor Portal
- **Registration**: Easy donor signup with blood group and location
- **Alert System**: Receive notifications for matching blood requests
- **Leaderboard**: Track top donors based on donation count
- **Availability Management**: Update availability status

### Patient Portal
- **Registration & Login**: Secure patient authentication
- **Blood Requests**: Submit urgent blood requests ("Blood Now")
- **Donor Matching**: Automatic matching with nearest available donors
- **Request History**: Track all blood requests and their status

### AI Integration
- AI Reports
- FAQ Bot

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: HTML/CSS/Bootstrap 5
- **Authentication**: Flask-Login
- **ORM**: SQLAlchemy
- **Icons**: Font Awesome

## 📋 Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd clotsync
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Start MySQL service
mysql -u root -p

# Create database and tables
source db_setup.sql
```

### 5. Configure Database Connection
Edit `app.py` and update the database URI:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/clotsync'
```

### 6. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 📊 Database Schema

### Tables
- **hospitals**: Hospital information and inventory
- **donors**: Donor registration and availability
- **patients**: Patient registration and authentication
- **requests**: Blood request tracking
- **transfers**: Hospital-to-hospital blood transfers
- **donor_alerts**: Alert system for donors

## 🔧 API Endpoints

### Hospital Routes
- `POST /register_hospital` - Hospital registration
- `POST /login_hospital` - Hospital login
- `POST /update_inventory` - Update blood inventory
- `GET /get_inventory/<hospital_id>` - Get hospital inventory
- `POST /transfer_blood` - Transfer blood between hospitals

### Donor Routes
- `POST /register_donor` - Donor registration
- `GET /find_donor/<blood_group>` - Find donors by blood group
- `GET /leaderboard` - Top donors leaderboard

### Patient Routes
- `POST /register_patient` - Patient registration
- `POST /login_patient` - Patient login
- `POST /request_blood` - Submit blood request

### AI/ML Routes
- `GET /predict_shortage` - Blood shortage predictions

## 🎯 Usage Guide

### For Hospitals
1. Register your hospital at `/register_hospital`
2. Login to access the dashboard
3. Update blood inventory as needed
4. View shortage predictions
5. Coordinate transfers with other hospitals

### For Donors
1. Register as a donor at `/register_donor`
2. Receive alerts for matching blood requests
3. Update availability status
4. View leaderboard rankings

### For Patients
1. Register as a patient at `/register_patient`
2. Login to access patient dashboard
3. Submit blood requests with urgency levels
4. Track request status and history

## 🔒 Security Features

- Password hashing with Werkzeug
- Session management with Flask-Login
- CSRF protection
- Input validation and sanitization
- Secure database connections

## 🎨 UI/UX Features

- Responsive Bootstrap 5 design
- Modern gradient backgrounds
- Interactive cards and hover effects
- Intuitive navigation
- Mobile-friendly interface
- Real-time updates

## 🚀 Deployment

### Production Setup
1. Use a production WSGI server (Gunicorn)
2. Set up a reverse proxy (Nginx)
3. Configure environment variables
4. Set up SSL certificates
5. Configure database backups

### Environment Variables
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export DATABASE_URL=mysql://user:pass@host/db
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔮 Future Enhancements

- Mobile app development
- SMS/Email notifications
- Advanced analytics dashboard
- Integration with blood banks
- Real-time tracking system
- Advanced ML predictions

---

**ClotSync** - Connecting lives through blood donation 🩸



