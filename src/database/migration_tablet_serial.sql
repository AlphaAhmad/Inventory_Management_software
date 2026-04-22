-- Migration: Add serial_number for tablets (especially iPads).
-- Tablets can have IMEI (with SIM) or no IMEI (WiFi only). iPads always need a serial number.
-- Run this in Supabase SQL Editor.

ALTER TABLE phone_details ADD COLUMN IF NOT EXISTS serial_number TEXT DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_phone_details_serial ON phone_details(serial_number);
