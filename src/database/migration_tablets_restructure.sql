-- Migration: Restructure Tablets category
-- Adds Tablets (devices) + Tablet Accessories (glass protectors, protector sheets, book covers, handle covers)

-- Step 1: Delete existing product types and their attribute definitions (no products exist)
DELETE FROM attribute_definitions WHERE product_type_id IN (
    SELECT pt.id FROM product_types pt
    JOIN subcategories s ON pt.subcategory_id = s.id
    WHERE s.category_id = (SELECT id FROM categories WHERE name = 'Tablet Accessories')
);

DELETE FROM product_types WHERE subcategory_id IN (
    SELECT id FROM subcategories WHERE category_id = (SELECT id FROM categories WHERE name = 'Tablet Accessories')
);

-- Step 2: Delete old subcategories
DELETE FROM subcategories WHERE category_id = (SELECT id FROM categories WHERE name = 'Tablet Accessories');

-- Step 3: Rename category to "Tablets"
UPDATE categories SET name = 'Tablets' WHERE name = 'Tablet Accessories';

-- Step 4: Create new subcategories
INSERT INTO subcategories (category_id, name, display_order) VALUES
    ((SELECT id FROM categories WHERE name = 'Tablets'), 'Tablets', 1),
    ((SELECT id FROM categories WHERE name = 'Tablets'), 'Glass Protectors', 2),
    ((SELECT id FROM categories WHERE name = 'Tablets'), 'Protector Sheets', 3),
    ((SELECT id FROM categories WHERE name = 'Tablets'), 'Book Covers', 4),
    ((SELECT id FROM categories WHERE name = 'Tablets'), 'Handle Covers', 5);

-- Step 5: Create product types under each subcategory

-- Tablets (devices)
INSERT INTO product_types (subcategory_id, name, display_order) VALUES
    ((SELECT id FROM subcategories WHERE name = 'Tablets' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'iPad', 1),
    ((SELECT id FROM subcategories WHERE name = 'Tablets' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Samsung Tablet', 2),
    ((SELECT id FROM subcategories WHERE name = 'Tablets' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Other Tablet', 3);

-- Glass Protectors
INSERT INTO product_types (subcategory_id, name, display_order) VALUES
    ((SELECT id FROM subcategories WHERE name = 'Glass Protectors' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'iPad Glass Protector', 1),
    ((SELECT id FROM subcategories WHERE name = 'Glass Protectors' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Samsung Tablet Glass Protector', 2),
    ((SELECT id FROM subcategories WHERE name = 'Glass Protectors' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Other Tablet Glass Protector', 3);

-- Protector Sheets (Clear and Mat)
INSERT INTO product_types (subcategory_id, name, display_order) VALUES
    ((SELECT id FROM subcategories WHERE name = 'Protector Sheets' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Clear Protector Sheet', 1),
    ((SELECT id FROM subcategories WHERE name = 'Protector Sheets' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Mat Protector Sheet', 2);

-- Book Covers
INSERT INTO product_types (subcategory_id, name, display_order) VALUES
    ((SELECT id FROM subcategories WHERE name = 'Book Covers' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'iPad Book Cover', 1),
    ((SELECT id FROM subcategories WHERE name = 'Book Covers' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Samsung Tablet Book Cover', 2),
    ((SELECT id FROM subcategories WHERE name = 'Book Covers' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Other Tablet Book Cover', 3);

-- Handle Covers
INSERT INTO product_types (subcategory_id, name, display_order) VALUES
    ((SELECT id FROM subcategories WHERE name = 'Handle Covers' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'iPad Handle Cover', 1),
    ((SELECT id FROM subcategories WHERE name = 'Handle Covers' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Samsung Tablet Handle Cover', 2),
    ((SELECT id FROM subcategories WHERE name = 'Handle Covers' AND category_id = (SELECT id FROM categories WHERE name = 'Tablets')), 'Other Tablet Handle Cover', 3);
