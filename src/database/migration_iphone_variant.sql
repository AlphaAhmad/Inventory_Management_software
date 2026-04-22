-- Migration: Add region_variant for iPhones
ALTER TABLE phone_details ADD COLUMN IF NOT EXISTS region_variant TEXT DEFAULT '';
