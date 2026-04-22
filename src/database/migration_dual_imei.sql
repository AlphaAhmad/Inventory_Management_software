-- Migration: Add dual IMEI support for phones
-- Run this in Supabase SQL Editor

-- Rename existing imei column to imei1
ALTER TABLE phone_details RENAME COLUMN imei TO imei1;

-- Add second IMEI column
ALTER TABLE phone_details ADD COLUMN IF NOT EXISTS imei2 TEXT DEFAULT '';

-- Add index for IMEI search
CREATE INDEX IF NOT EXISTS idx_phone_details_imei1 ON phone_details(imei1);
CREATE INDEX IF NOT EXISTS idx_phone_details_imei2 ON phone_details(imei2);
