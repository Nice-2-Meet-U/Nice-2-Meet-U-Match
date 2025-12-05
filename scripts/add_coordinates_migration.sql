-- Migration: Add coord_x and coord_y to pool_members table
-- Date: 2025-11-30

ALTER TABLE pool_members 
ADD COLUMN coord_x FLOAT NULL,
ADD COLUMN coord_y FLOAT NULL;

-- Verify the migration
DESCRIBE pool_members;
