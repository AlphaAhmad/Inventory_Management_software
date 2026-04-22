-- Migration: Add return/claim support
-- Run this in Supabase SQL Editor

-- 1. Widen transaction type CHECK to include return/claim types
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_type_check;
ALTER TABLE transactions ADD CONSTRAINT transactions_type_check
    CHECK (type IN ('purchase', 'sale', 'return', 'claim', 'claim_resolved'));

-- 2. Add related_transaction_id for linking returns to sales, claims to sales, etc.
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS related_transaction_id UUID REFERENCES transactions(id);

-- 3. Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_transactions_related ON transactions(related_transaction_id);
