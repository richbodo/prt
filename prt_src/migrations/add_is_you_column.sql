-- Migration to add is_you and name split columns to contacts table
-- This flag marks the special "You" contact for the application

ALTER TABLE contacts ADD COLUMN is_you BOOLEAN DEFAULT FALSE;
ALTER TABLE contacts ADD COLUMN first_name VARCHAR(100);
ALTER TABLE contacts ADD COLUMN last_name VARCHAR(100);

-- Create index for quick lookup of the "You" contact
CREATE INDEX idx_contacts_is_you ON contacts(is_you) WHERE is_you = TRUE;

-- Populate first_name and last_name from existing name field
UPDATE contacts SET 
    first_name = CASE 
        WHEN POSITION(' ' IN name) > 0 THEN SUBSTRING(name FROM 1 FOR POSITION(' ' IN name) - 1)
        ELSE name
    END,
    last_name = CASE 
        WHEN POSITION(' ' IN name) > 0 THEN SUBSTRING(name FROM POSITION(' ' IN name) + 1)
        ELSE ''
    END;