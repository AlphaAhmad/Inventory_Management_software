-- Inventory Management System Schema
-- Run this in Supabase SQL Editor to create all tables

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Categories (top-level grouping)
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    display_order INT DEFAULT 0
);

-- 2. Subcategories (second level)
CREATE TABLE IF NOT EXISTS subcategories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    display_order INT DEFAULT 0,
    UNIQUE(category_id, name)
);

-- 3. Product types (third level - the actual item type)
CREATE TABLE IF NOT EXISTS product_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subcategory_id UUID NOT NULL REFERENCES subcategories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    display_order INT DEFAULT 0,
    UNIQUE(subcategory_id, name)
);

-- 4. Attribute definitions (dynamic form fields per product type)
CREATE TABLE IF NOT EXISTS attribute_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_type_id UUID NOT NULL REFERENCES product_types(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    label TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK (field_type IN ('text', 'number', 'boolean', 'select')),
    options JSONB DEFAULT '[]'::jsonb,
    is_required BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    UNIQUE(product_type_id, name)
);

-- 5. Products (actual inventory items)
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_type_id UUID NOT NULL REFERENCES product_types(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    brand TEXT DEFAULT '',
    model TEXT DEFAULT '',
    purchase_price DECIMAL(12,2) DEFAULT 0,
    sale_price DECIMAL(12,2) DEFAULT 0,
    quantity INT DEFAULT 0,
    status TEXT DEFAULT 'in_stock' CHECK (status IN ('in_stock', 'sold', 'claimed')),
    attributes JSONB DEFAULT '{}'::jsonb,
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Transactions (buy/sell records)
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('purchase', 'sale', 'return', 'claim', 'claim_resolved')),
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    original_price DECIMAL(12,2) DEFAULT 0,
    customer_info TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    related_transaction_id UUID REFERENCES transactions(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Phone details (specialized fields for phones)
CREATE TABLE IF NOT EXISTS phone_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID UNIQUE NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    imei1 TEXT DEFAULT '',
    imei2 TEXT DEFAULT '',
    phone_type TEXT NOT NULL CHECK (phone_type IN ('used', 'box_pack', 'keypad')),
    has_box BOOLEAN DEFAULT FALSE,
    has_charger BOOLEAN DEFAULT FALSE,
    keypad_type TEXT DEFAULT '' CHECK (keypad_type IN ('', 'keys_only', 'keypad_touchscreen')),
    is_claimed BOOLEAN DEFAULT FALSE,
    claim_reason TEXT DEFAULT '',
    condition TEXT DEFAULT '' CHECK (condition IN ('', 'excellent', 'good', 'fair', 'poor')),
    storage_gb INT DEFAULT 0,
    ram_gb INT DEFAULT 0,
    color TEXT DEFAULT '',
    region_variant TEXT DEFAULT '',
    serial_number TEXT DEFAULT ''
);

-- Index for faster product lookups
CREATE INDEX IF NOT EXISTS idx_products_product_type_id ON products(product_type_id);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_transactions_product_id ON transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);

-- Auto-update updated_at on products
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROWs
    EXECUTE FUNCTION update_updated_at_column();
