-- Migration: Add original_price to transactions for tracking haggled prices
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS original_price DECIMAL(12,2) DEFAULT 0;
