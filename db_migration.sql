-- Database Migration Script for ClotSync
-- Add user_type columns to distinguish between user types

-- Add user_type column to hospitals table
ALTER TABLE hospitals ADD COLUMN user_type VARCHAR(20) DEFAULT 'hospital';

-- Add user_type column to donors table  
ALTER TABLE donors ADD COLUMN user_type VARCHAR(20) DEFAULT 'donor';

-- Add user_type column to patients table
ALTER TABLE patients ADD COLUMN user_type VARCHAR(20) DEFAULT 'patient';

-- Update existing records to have proper user_type
UPDATE hospitals SET user_type = 'hospital' WHERE user_type IS NULL;
UPDATE donors SET user_type = 'donor' WHERE user_type IS NULL;
UPDATE patients SET user_type = 'patient' WHERE user_type IS NULL;

-- Verify the changes
SELECT 'hospitals' as table_name, COUNT(*) as count, user_type FROM hospitals GROUP BY user_type
UNION ALL
SELECT 'donors' as table_name, COUNT(*) as count, user_type FROM donors GROUP BY user_type
UNION ALL
SELECT 'patients' as table_name, COUNT(*) as count, user_type FROM patients GROUP BY user_type;

