-- Create database
CREATE DATABASE IF NOT EXISTS clotsync;
USE clotsync;

-- Hospitals table
CREATE TABLE IF NOT EXISTS hospitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    inventory TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Donors table
CREATE TABLE IF NOT EXISTS donors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    blood_group VARCHAR(25) NOT NULL,
    location VARCHAR(200) NOT NULL,
    contact VARCHAR(20) NOT NULL,
    availability BOOLEAN DEFAULT TRUE,
    donations_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    eligibility_status VARCHAR(20) DEFAULT 'eligible'
);

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    blood_group VARCHAR(25) NOT NULL,
    location VARCHAR(200) NOT NULL,
    contact VARCHAR(20) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blood requests table
CREATE TABLE IF NOT EXISTS requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    blood_group VARCHAR(25) NOT NULL,
    urgency VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending',
    units_needed INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Blood transfers table (ledger)
CREATE TABLE IF NOT EXISTS transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    from_hospital_id INT NOT NULL,
    to_hospital_id INT NOT NULL,
    blood_group VARCHAR(25) NOT NULL,
    units INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (from_hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (to_hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- Donor alerts table
CREATE TABLE IF NOT EXISTS donor_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    request_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES donors(id) ON DELETE CASCADE,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
);

-- Insert sample data with new blood group format
INSERT INTO hospitals (name, location, username, password, inventory) VALUES
('City General Hospital', 'Downtown, City Center', 'city_hospital', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8K2', '{"A Positive": 50, "A Negative": 30, "B Positive": 45, "B Negative": 25, "AB Positive": 20, "A2B Negative": 15, "O Positive": 60, "O Negative": 40}'),
('Metro Medical Center', 'North District', 'metro_medical', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8K2', '{"A Positive": 35, "A Negative": 20, "B Positive": 40, "B Negative": 18, "AB Positive": 15, "A2B Negative": 10, "O Positive": 45, "O Negative": 30}');

INSERT INTO donors (name, blood_group, location, contact, availability, donations_count) VALUES
('John Smith', 'A Positive', 'Downtown, City Center', '+1234567890', TRUE, 5),
('Sarah Johnson', 'O Negative', 'North District', '+1234567891', TRUE, 8),
('Mike Wilson', 'B Positive', 'East Side', '+1234567892', TRUE, 3),
('Emily Davis', 'AB Positive', 'West End', '+1234567893', FALSE, 2),
('David Brown', 'O Positive', 'South District', '+1234567894', TRUE, 6);

INSERT INTO patients (name, blood_group, location, contact, username, password) VALUES
('Alice Cooper', 'A Positive', 'Downtown, City Center', '+1234567895', 'alice_cooper', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8K2'),
('Bob Miller', 'O Negative', 'North District', '+1234567896', 'bob_miller', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8K2');

-- Create indexes for better performance
CREATE INDEX idx_donors_blood_group ON donors(blood_group);
CREATE INDEX idx_donors_availability ON donors(availability);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_blood_group ON requests(blood_group);
CREATE INDEX idx_transfers_timestamp ON transfers(timestamp);

