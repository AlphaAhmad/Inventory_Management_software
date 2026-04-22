-- Migration: Add region_variant to phone_details
ALTER TABLE phone_details ADD COLUMN IF NOT EXISTS region_variant TEXT DEFAULT '';
