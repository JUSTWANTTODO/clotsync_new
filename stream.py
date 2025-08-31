import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import warnings
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Blood Donor Reliability Predictor",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ============================= */
/* GLOBAL STYLES */
/* ============================= */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html, body, [class*="stApp"] {
    background: linear-gradient(145deg, #000000, #0d0d0d);
    color: #ffffff;
    font-family: 'Poppins', sans-serif;
}

h1, h2, h3, h4 {
    color: #ffffff !important;
    font-weight: 600;
}

/* ============================= */
/* HEADER & SUBTITLE */
/* ============================= */
.main-header {
    font-size: 2.8rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(90deg, #ff416c, #ff4b2b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    text-shadow: 0px 4px 20px rgba(255, 75, 43, 0.5);
}

.subtitle {
    text-align: center;
    font-size: 1rem;
    font-weight: 400;
    color: #a1a1aa;
    margin-bottom: 2.5rem;
}

/* ============================= */
/* STATS CARDS */
/* ============================= */
.stats-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    padding: 1rem;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    text-align: center;
    transition: all 0.3s ease-in-out;
    box-shadow: 0 4px 20px rgba(255,255,255,0.05);
}

.stats-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(255,75,43,0.2);
}

.stats-number {
    font-size: 1.8rem;
    font-weight: 700;
    color: #ff4b2b;
}

.stats-label {
    font-size: 0.8rem;
    color: #d1d5db;
    text-transform: uppercase;
}

/* ============================= */
/* FORM INPUTS */
/* ============================= */
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stDateInput > div > div > input,
.stRadio > div {
    background: rgba(255,255,255,0.05) !important;
    color: #fff !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    text-align: center !important;
    font-weight: 500;
}

.stSelectbox label, .stNumberInput label, .stDateInput label {
    color: #ffffff !important;
    font-weight: 500;
}

/* ============================= */
/* BUTTONS */
/* ============================= */
.stButton button {
    background: linear-gradient(90deg, #ff416c, #ff4b2b);
    color: white;
    font-weight: 600;
    padding: 0.9rem 2rem;
    border-radius: 12px;
    border: none;
    font-size: 1rem;
    box-shadow: 0 4px 20px rgba(255,75,43,0.3);
    transition: all 0.3s ease-in-out;
}

.stButton button:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 30px rgba(255,75,43,0.5);
}

/* ============================= */
/* RESULT BOXES */
/* ============================= */
.reliable-box, .not-reliable-box {
    border-radius: 16px;
    padding: 1.8rem;
    text-align: center;
    margin: 2rem 0;
    font-weight: 600;
    font-size: 1.1rem;
}

.reliable-box {
    background: rgba(34,197,94,0.1);
    border: 1px solid #22c55e;
    box-shadow: 0 4px 25px rgba(34,197,94,0.3);
}

.not-reliable-box {
    background: rgba(239,68,68,0.1);
    border: 1px solid #ef4444;
    box-shadow: 0 4px 25px rgba(239,68,68,0.3);
}

.confidence-badge {
    background: linear-gradient(90deg, #3b82f6, #1d4ed8);
    padding: 0.4rem 1rem;
    border-radius: 25px;
    font-size: 0.9rem;
    box-shadow: 0 4px 15px rgba(59,130,246,0.3);
}

/* ============================= */
/* PROFESSIONAL DONOR DETAILS TABLE */
/* ============================= */
.donor-details-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-size: 0.85rem;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
}

.donor-details-table th {
    background: rgba(255,75,43,0.2);
    padding: 0.8rem;
    text-align: left;
    font-weight: 600;
    color: #ff4b2b;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.donor-details-table td {
    padding: 0.7rem 0.8rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.donor-details-table tr:last-child td {
    border-bottom: none;
}

.donor-details-table tr:hover {
    background: rgba(255,255,255,0.02);
}

/* ============================= */
/* FEATURE IMPORTANCE SECTION */
/* ============================= */
.feature-importance {
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 1.2rem;
    margin: 1.5rem 0;
    border: 1px solid rgba(255,255,255,0.1);
}

.feature-importance h4 {
    color: #ff4b2b !important;
    margin-bottom: 0.8rem;
    font-size: 1rem;
}

.feature-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.feature-item:last-child {
    border-bottom: none;
}

.feature-name {
    font-size: 0.85rem;
    color: #d1d5db;
}

.feature-value {
    font-size: 0.85rem;
    font-weight: 600;
    color: #ff4b2b;
}

/* ============================= */
/* FOOTER */
/* ============================= */
footer, .css-164nlkn, .css-qri22k {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# Add confidence bar CSS
st.markdown("""
<style>
.confidence-bar-container {
    width: 100%;
    max-width: 300px;
    height: 22px;
    background: #222;
    border-radius: 12px;
    border: 1px solid #3b82f6;
    margin: 0.7rem auto 0.7rem auto;
    box-shadow: 0 2px 8px rgba(59,130,246,0.15);
    position: relative;
}
.confidence-bar-fill {
    height: 100%;
    border-radius: 12px;
    background: linear-gradient(90deg, #3b82f6, #1d4ed8);
    transition: width 0.6s cubic-bezier(.4,0,.2,1);
}
.confidence-bar-label {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    color: #fff;
    font-weight: 600;
    font-size: 0.95rem;
    letter-spacing: 0.5px;
    text-shadow: 0 2px 8px rgba(59,130,246,0.15);
}
</style>
""", unsafe_allow_html=True)

class BloodDonorPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = None
        
    def preprocess_data(self, df):
        """Preprocess the raw donor data"""
        df_clean = df.copy()
        
        # Store original categorical values for display
        self.original_categorical_values = {}
        
        # Handle date columns
        date_columns = ['last_donation_date', 'next_eligible_date']
        for col in date_columns:
            df_clean[col] = df_clean[col].replace('', pd.NaT)
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        
        # Handle numeric columns with 'Not applicable'
        numeric_columns = ['quantity_required', 'donations_till_date', 'cycle_of_donations', 
                          'frequency_days_for_tranfusion']
        
        for col in numeric_columns:
            df_clean[col] = df_clean[col].replace('Not applicable', np.nan)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Create is_reliable feature
        df_clean['is_reliable'] = df_clean.apply(self._calculate_reliability, axis=1)
        
        # Feature engineering
        df_clean['days_since_last_donation'] = (pd.Timestamp.today() - df_clean['last_donation_date']).dt.days
        df_clean['days_since_last_donation'] = df_clean['days_since_last_donation'].fillna(365*5)
        
        df_clean['days_until_eligible'] = (df_clean['next_eligible_date'] - pd.Timestamp.today()).dt.days
        df_clean['days_until_eligible'] = df_clean['days_until_eligible'].fillna(0)
        
        df_clean['is_currently_eligible'] = (df_clean['days_until_eligible'] <= 0).astype(int)
        
        # Handle categorical variables
        categorical_cols = ['role', 'blood_group', 'gender', 'type_of_donor']
        
        for col in categorical_cols:
            if col in df_clean.columns:
                if df_clean[col].isnull().any():
                    df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0])
                
                # Store original values for display
                self.original_categorical_values[col] = df_clean[col].copy()
                
                # Create and store label encoder
                self.label_encoders[col] = LabelEncoder()
                df_clean[col] = self.label_encoders[col].fit_transform(df_clean[col].astype(str))
        
        # Handle donated_earlier
        df_clean['donated_earlier'] = df_clean['donated_earlier'].map({'TRUE': 1, 'FALSE': 0})
        
        # Fill remaining missing values
        numeric_cols = ['quantity_required', 'donations_till_date', 'cycle_of_donations', 
                       'frequency_days_for_tranfusion', 'latitude', 'longitude']
        
        for col in numeric_cols:
            if col in df_clean.columns and df_clean[col].isnull().any():
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
        
        # Drop unnecessary columns
        columns_to_drop = ['last_transfusion_date', 'expected_next_transfusion_date', 
                          'last_donation_date', 'next_eligible_date']
        
        for col in columns_to_drop:
            if col in df_clean.columns:
                df_clean = df_clean.drop(col, axis=1)
        
        # Store feature columns for later use
        self.feature_columns = [col for col in df_clean.columns if col != 'is_reliable']
        
        return df_clean
    
    def _calculate_reliability(self, row):
        """Calculate reliability score for a donor"""
        reliability_score = 0
        
        # Regular donors are more reliable
        if row['type_of_donor'] == 'Regular Donor':
            reliability_score += 3
        elif row['type_of_donor'] == 'One-Time Donor':
            reliability_score += 1
        
        # More donations indicate reliability
        if pd.notna(row['donations_till_date']):
            reliability_score += min(row['donations_till_date'] / 2, 5)
        
        # Recent donation indicates reliability
        if pd.notna(row['last_donation_date']):
            days_since_last_donation = (pd.Timestamp.today() - row['last_donation_date']).days
            if days_since_last_donation <= 90:
                reliability_score += 2
            elif days_since_last_donation <= 180:
                reliability_score += 1
        
        # Donated earlier indicates experience
        if row['donated_earlier'] == 'TRUE':
            reliability_score += 2
        
        # Bridge donors are typically more reliable than emergency
        if row['role'] == 'Bridge Donor':
            reliability_score += 2
        elif row['role'] == 'Volunteer':
            reliability_score += 1
        
        return 1 if reliability_score >= 5 else 0
    
    def train_model(self, X, y):
        """Train the Random Forest model"""
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        return self.model
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate model performance"""
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
            
        y_pred = self.model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        cm = confusion_matrix(y_test, y_pred)
        
        return accuracy, report, cm, y_pred
    
    def save_model(self, filepath='blood_donor_model.pkl'):
        """Save the trained model and preprocessing objects"""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
            
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns
        }
        
        joblib.dump(model_data, filepath)
        return filepath
    
    def load_model(self, filepath='blood_donor_model.pkl'):
        """Load a trained model and preprocessing objects"""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_columns = model_data['feature_columns']
        
        return self
    
    def predict_single_donor(self, donor_data):
        """Predict reliability for a single donor"""
        if self.model is None:
            raise ValueError("No model loaded. Train or load a model first.")
            
        # Convert input to DataFrame
        input_df = pd.DataFrame([donor_data])
        
        # Preprocess the input
        processed_input = self._preprocess_single_input(input_df)
        
        # Make prediction
        probability = self.model.predict_proba(processed_input)[0][1]
        prediction = self.model.predict(processed_input)[0]
        
        # Get feature importance for this prediction
        feature_importance = self._get_feature_importance(input_df)
        
        return {
            'reliable': bool(prediction),
            'confidence': float(probability),
            'message': 'Reliable donor' if prediction else 'Needs verification',
            'feature_importance': feature_importance
        }
    
    def _preprocess_single_input(self, input_df):
        """Preprocess a single donor input"""
        # Handle dates
        input_df['last_donation_date'] = pd.to_datetime(input_df['last_donation_date'], errors='coerce')
        input_df['next_eligible_date'] = pd.to_datetime(input_df['next_eligible_date'], errors='coerce')
        
        # Feature engineering
        input_df['days_since_last_donation'] = (pd.Timestamp.today() - input_df['last_donation_date']).dt.days
        input_df['days_since_last_donation'] = input_df['days_since_last_donation'].fillna(365*5)
        
        input_df['days_until_eligible'] = (input_df['next_eligible_date'] - pd.Timestamp.today()).dt.days
        input_df['days_until_eligible'] = input_df['days_until_eligible'].fillna(0)
        
        input_df['is_currently_eligible'] = (input_df['days_until_eligible'] <= 0).astype(int)
        
        # Encode categorical variables
        for col, encoder in self.label_encoders.items():
            if col in input_df.columns:
                # Handle unseen labels by using the most common class
                input_df[col] = input_df[col].apply(lambda x: x if x in encoder.classes_ else encoder.classes_[0])
                input_df[col] = encoder.transform(input_df[col])
        
        # Handle donated_earlier
        if 'donated_earlier' in input_df.columns:
            input_df['donated_earlier'] = input_df['donated_earlier'].map({'TRUE': 1, 'FALSE': 0, True: 1, False: 0})
            input_df['donated_earlier'] = input_df['donated_earlier'].fillna(0)
        
        # Select only the features used during training
        processed_input = input_df[self.feature_columns].copy()
        
        # Scale the features
        processed_input_scaled = self.scaler.transform(processed_input)
        
        return processed_input_scaled
    
    def _get_feature_importance(self, input_df):
        """Get feature importance for the prediction"""
        if self.model is None:
            return {}
        
        # Get feature importances
        importances = self.model.feature_importances_
        feature_names = self.feature_columns
        
        # Create a dictionary of feature importance
        importance_dict = dict(zip(feature_names, importances))
        
        # Map to human-readable feature names
        readable_names = {
            'role': 'Donor Type',
            'blood_group': 'Blood Group',
            'gender': 'Gender',
            'donations_till_date': 'Previous Donations',
            'days_since_last_donation': 'Days Since Last Donation',
            'days_until_eligible': 'Days Until Eligible',
            'is_currently_eligible': 'Currently Eligible',
            'type_of_donor': 'Donor Category',
            'donated_earlier': 'Donated Before'
        }
        
        # Return top 5 most important features for this prediction
        sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {readable_names.get(k, k): round(v, 4) for k, v in sorted_features}

def create_dashboard_charts(df_processed, predictor):
    """Create interactive charts for the dashboard"""
    charts = {}
    
    # Blood Group Distribution - use original values
    blood_group_original = predictor.original_categorical_values['blood_group'].replace({
        'A Positive': 'A+', 'A Negative': 'A-',
        'B Positive': 'B+', 'B Negative': 'B-',
        'AB Positive': 'AB+', 'AB Negative': 'AB-',
        'O Positive': 'O+', 'O Negative': 'O-', 'A1B Positive': 'A1B+', 'A1 Positive': 'A1+'
    })
    blood_group_counts = blood_group_original.value_counts()
    fig_blood = px.pie(
        values=blood_group_counts.values, 
        names=blood_group_counts.index,
        title="Blood Group Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_blood.update_layout(
        title_x=0.5,
        title_font_size=12,
        showlegend=True,
        height=250,
        width=300,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    charts['blood_group'] = fig_blood
    
    # Donor Type Distribution - use original values
    donor_type_original = predictor.original_categorical_values['type_of_donor']
    donor_type_counts = donor_type_original.value_counts()
    fig_donor = px.bar(
        x=donor_type_counts.index,
        y=donor_type_counts.values,
        title="Donor Type Distribution",
        color=donor_type_counts.values,
        color_continuous_scale='Blues'
    )
    fig_donor.update_layout(
        title_x=0.5,
        title_font_size=12,
        xaxis_title="Donor Type",
        yaxis_title="Count",
        height=250,
        width=300,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    charts['donor_type'] = fig_donor
    
    # Reliability by Role - use original values
    role_original = predictor.original_categorical_values['role']
    reliability_by_role = pd.DataFrame({
        'role': role_original,
        'is_reliable': df_processed['is_reliable']
    }).groupby('role')['is_reliable'].mean().reset_index()
    
    fig_role = px.bar(
        x=reliability_by_role['role'],
        y=reliability_by_role['is_reliable'],
        title="Reliability Rate by Donor Role",
        color=reliability_by_role['is_reliable'],
        color_continuous_scale='RdYlGn'
    )
    fig_role.update_layout(
        title_x=0.5,
        title_font_size=12,
        xaxis_title="Donor Role",
        yaxis_title="Reliability Rate",
        height=250,
        width=300,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    charts['reliability_role'] = fig_role
    
    return charts

def main():
    # Hero Section
    st.markdown('<h1 class="main-header">🩸Blood Donor Reliability Predictor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Advanced AI-powered system to assess blood donor reliability and optimize blood bank operations</p>', unsafe_allow_html=True)
    
    # Backend: Load and train model on startup (only once)
    if 'predictor' not in st.session_state:
        st.session_state.predictor = BloodDonorPredictor()
        # Load backend dataset
        backend_csv = os.path.join(os.path.dirname(__file__), 'hack_data.csv')
        df = pd.read_csv(backend_csv)
        df_processed = st.session_state.predictor.preprocess_data(df)
        X = df_processed.drop('is_reliable', axis=1)
        y = df_processed['is_reliable']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train_scaled = st.session_state.predictor.scaler.fit_transform(X_train)
        st.session_state.predictor.train_model(X_train_scaled, y_train)
        st.session_state.model_trained = True
        st.session_state.df_processed = df_processed
    
    # Dashboard Statistics
    if 'df_processed' in st.session_state:
        df_processed = st.session_state.df_processed
        
        # Calculate statistics
        total_donors = len(df_processed)
        reliable_donors = df_processed['is_reliable'].sum()
        reliability_rate = (reliable_donors / total_donors) * 100
        avg_donations = df_processed['donations_till_date'].mean()
        
        # Display stats in cards with better spacing
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-number">📊 {total_donors:,}</div>
                <div class="stats-label">Total Donors</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-number">✅ {reliable_donors:,}</div>
                <div class="stats-label">Reliable Donors</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-number">📈 {reliability_rate:.1f}%</div>
                <div class="stats-label">Reliability Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-number">🔄 {avg_donations:.1f}</div>
                <div class="stats-label">Avg Donations Per Donor</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Charts Section
    if 'df_processed' in st.session_state:
        st.markdown('<div style="margin-top:2.5rem;"></div>', unsafe_allow_html=True)
        st.markdown('<h2 class="chart-title">📊 Data Analytics Dashboard</h2>', unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:2.2rem;"></div>', unsafe_allow_html=True)
        charts = create_dashboard_charts(st.session_state.df_processed, st.session_state.predictor)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(charts['blood_group'], use_container_width=True)
        with col2:
            st.plotly_chart(charts['donor_type'], use_container_width=True)
        with col3:
            st.plotly_chart(charts['reliability_role'], use_container_width=True)

    # Prediction Form
    st.markdown('<div style="margin-top:2.5rem;"></div>', unsafe_allow_html=True)
    st.markdown('<h2 class="form-title">🔮 Predict Donor Reliability</h2>', unsafe_allow_html=True)
    st.markdown('<div style="margin-bottom:2.2rem;"></div>', unsafe_allow_html=True)
    
    # Personal Information Section
    st.markdown('<h3 class="form-section-title">Personal Information</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        role = st.selectbox("Donor Type", ["Emergency Donor", "Bridge Donor", "Volunteer"], key="role_select")
        
        # Update blood group input dropdown options to use A+, A-, etc.
        blood_group_options = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        blood_group = st.selectbox("Blood Group", blood_group_options, key="blood_select")
    
    with col2:
        gender = st.selectbox("⚧ Gender", ["Male", "Female"], key="gender_select")
        type_of_donor = st.selectbox("Type of Donor", ["Regular Donor", "One-Time Donor", "Other"], key="donor_select")
    
    # Donation History Section
    st.markdown('<h3 class="form-section-title">Donation History</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        donations_till_date = st.number_input("Number of Previous Donations", min_value=0, max_value=100, value=1, key="donations_input")
    
    with col2:
        # Donated earlier logic: radio always visible, auto-select based on donations_till_date
        donated_radio_default = "TRUE" if donations_till_date > 0 else "FALSE"
        donated_earlier = st.radio(
            "Has donated before?",
            ["TRUE", "FALSE"],
            horizontal=True,
            index=0 if donated_radio_default == "TRUE" else 1,
            key="donated_radio"
        )
    
    # Last Donation Date and Next Eligible Date logic
    if donations_till_date == 0:
        last_donation_date = None
        next_eligible_date = None
        st.markdown("<div style='color:#a1a1aa;font-size:0.95rem;margin-bottom:0.5rem;'>No donation history, so Last Donation Date and Next Eligible Date are not applicable. Prediction will use other available information.</div>", unsafe_allow_html=True)
        last_donation_date_str = ''
        next_eligible_date_str = ''
    else:
        last_donation_date = st.date_input("Last Donation Date", value=date.today(), key="last_donation")
        # Calculate minimum eligible date based on gender
        min_eligible_days = 90 if gender == "Male" else 120
        min_eligible_date = last_donation_date + pd.Timedelta(days=min_eligible_days)
        next_eligible_date = st.date_input(
            f"Next Eligible Date (min {min_eligible_days//30} months after last donation)",
            value=min_eligible_date,
            min_value=min_eligible_date,
            key="next_eligible"
        )
        last_donation_date_str = last_donation_date.strftime('%Y-%m-%d')
        next_eligible_date_str = next_eligible_date.strftime('%Y-%m-%d')
    
    # After calculating next_eligible_date, check if it's before today
    from datetime import datetime
    if donations_till_date > 0 and next_eligible_date is not None:
        if next_eligible_date < datetime.today().date():
            st.markdown("<div style='color:#22c55e;font-weight:600;margin-bottom:0.5rem;'>Y are eligible to donate from today!</div>", unsafe_allow_html=True)
    
    # Default values for other fields
    donor_data = {
        'role': role,
        'blood_group': blood_group,
        'gender': gender,
        'latitude': 17.3922792,
        'longitude': 78.4602749,
        'quantity_required': 0,
        'last_transfusion_date': 'Not applicable',
        'expected_next_transfusion_date': 'Not applicable',
        'donations_till_date': donations_till_date,
        'cycle_of_donations': 90,
        'frequency_days_for_tranfusion': 30,
        'type_of_donor': type_of_donor,
        'last_donation_date': last_donation_date_str,
        'next_eligible_date': next_eligible_date_str,
        'donated_earlier': donated_earlier
    }
    
    # Prediction Button
    show_details = False  # Only show donor details summary table after prediction
    if st.button("Predict Reliability", type="primary"):
        # Validation checks
        if donations_till_date > 0 and donated_earlier == "FALSE":
            st.error("❌ If number of donations is more than 0, 'Has donated before?' must be TRUE.")
            return
        # No validation block for missing dates if donations_till_date == 0
        if donations_till_date > 0:
            min_eligible_days = 90 if gender == "Male" else 120
            min_eligible_date = last_donation_date + pd.Timedelta(days=min_eligible_days)
            # In prediction button logic, only check next_eligible_date < min_eligible_date if both are not None
            if next_eligible_date is not None and min_eligible_date is not None:
                if next_eligible_date < min_eligible_date:
                    st.error(f"❌ Next eligible date must be at least {min_eligible_days//30} months after last donation for {gender.lower()}s.")
                    return
        # Show loading spinner
        with st.spinner("🔍 Analyzing donor data..."):
            try:
                result = st.session_state.predictor.predict_single_donor(donor_data)
                show_details = True
                
                if result['reliable']:
                    st.markdown(f"""
                    <div class="reliable-box">
                        <span class="result-icon">✅</span>
                        <h2>Reliable Donor</h2>
                        <div class="confidence-bar-container">
                            <div class="confidence-bar-fill" style="width: {result['confidence']*100:.1f}%;"></div>
                            <span class="confidence-bar-label">Confidence: {result['confidence']*100:.1f}%</span>
                        </div>
                        <p style="font-size: 1.1rem; margin: 1rem 0;">This donor is likely to be reliable based on their history and characteristics.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="not-reliable-box">
                        <span class="result-icon">⚠️</span>
                        <h2>Needs Verification</h2>
                        <div class="confidence-bar-container">
                            <div class="confidence-bar-fill" style="width: {result['confidence']*100:.1f}%;"></div>
                            <span class="confidence-bar-label">Confidence: {result['confidence']*100:.1f}%</span>
                        </div>
                        <p style="font-size: 1.1rem; margin: 1rem 0;">This donor may need additional verification before relying on them.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Only show donor details summary table after prediction
                if show_details:
                    st.markdown('<h3 style="color: #ffffff; margin: 2rem 0 1rem 0;">📋 Donor Details Summary</h3>', unsafe_allow_html=True)
                    
                    # Render donor details summary as a flexible HTML table
                    blood_group_display = blood_group
                    last_donation_display = last_donation_date_str if last_donation_date_str else '-'
                    next_eligible_display = next_eligible_date_str if next_eligible_date_str else '-'
                    st.markdown(f"""
                    <table style='width:100%;max-width:700px;margin:1.5rem auto;border-collapse:collapse;'>
                        <thead>
                            <tr style='background:rgba(255,255,255,0.07);'>
                                <th style='padding:8px 12px;text-align:left;font-weight:700;color:#a1a1aa;'>Attribute</th>
                                <th style='padding:8px 12px;text-align:left;font-weight:700;color:#a1a1aa;'>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td style='padding:8px 12px;'>Donor Type</td><td style='padding:8px 12px;'>{role}</td></tr>
                            <tr><td style='padding:8px 12px;'>Blood Group</td><td style='padding:8px 12px;'>{blood_group_display}</td></tr>
                            <tr><td style='padding:8px 12px;'>Gender</td><td style='padding:8px 12px;'>{gender}</td></tr>
                            <tr><td style='padding:8px 12px;'>Donor Category</td><td style='padding:8px 12px;'>{type_of_donor}</td></tr>
                            <tr><td style='padding:8px 12px;'>Total Donations</td><td style='padding:8px 12px;'>{donations_till_date}</td></tr>
                            <tr><td style='padding:8px 12px;'>Last Donation</td><td style='padding:8px 12px;'>{last_donation_display}</td></tr>
                            <tr><td style='padding:8px 12px;'>Next Eligible</td><td style='padding:8px 12px;'>{next_eligible_display}</td></tr>
                            <tr><td style='padding:8px 12px;'>Previous Donor</td><td style='padding:8px 12px;'>{donated_earlier}</td></tr>
                        </tbody>
                    </table>
                    """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error making prediction: {str(e)}")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #64748b; font-size: 0.85rem; border-top: 1px solid #e2e8f0; margin-top: 2rem;">
        <p>Blood Donor Reliability Predictor | Powered by Machine Learning & AI</p>
        <p>Built with ❤️ for better blood bank management</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()