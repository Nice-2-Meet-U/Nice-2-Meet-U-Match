-- SQL to rename matches.id to matches.match_id and update all foreign key references
-- Run this manually in your MySQL database

-- Step 1: Drop foreign key constraint from match_decisions
ALTER TABLE match_decisions 
DROP FOREIGN KEY match_decisions_ibfk_1;

-- Step 2: Rename the column in matches table
ALTER TABLE matches 
CHANGE COLUMN id match_id CHAR(36) NOT NULL;

-- Step 3: Re-add foreign key constraint with new column name
ALTER TABLE match_decisions 
ADD CONSTRAINT match_decisions_ibfk_1 
FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE;

-- Step 4: Verify the changes
SHOW CREATE TABLE matches;
SHOW CREATE TABLE match_decisions;
