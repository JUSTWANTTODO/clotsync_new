-- Fix blood_group column size from VARCHAR(3) to VARCHAR(25)
-- This is needed to accommodate blood groups like "Bombay Blood Group" (18 characters)

-- Update donors table
ALTER TABLE donors MODIFY COLUMN blood_group VARCHAR(25) NOT NULL;

-- Update patients table  
ALTER TABLE patients MODIFY COLUMN blood_group VARCHAR(25) NOT NULL;

-- Update requests table
ALTER TABLE requests MODIFY COLUMN blood_group VARCHAR(25) NOT NULL;

-- Verify the changes
DESCRIBE donors;
DESCRIBE patients;
DESCRIBE requests;
