-- Add eligibility_status column to donors table
-- This column will store 'eligible' or 'not eligible' based on donation intervals

-- Add the new column
ALTER TABLE donors ADD COLUMN eligibility_status VARCHAR(20) DEFAULT 'eligible';

-- Update existing donors with eligibility status
-- This will set all existing donors to 'eligible' initially
UPDATE donors SET eligibility_status = 'eligible' WHERE eligibility_status IS NULL;

-- Create an index for better performance on eligibility queries
CREATE INDEX idx_donors_eligibility_status ON donors(eligibility_status);

-- Verify the changes
DESCRIBE donors;
