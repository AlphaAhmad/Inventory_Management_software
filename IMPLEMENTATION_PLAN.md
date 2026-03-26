# Inventory Management System - Implementation Plan
## Mobile Phone Shop - Desktop Application

---

## Context

A mobile phone shop needs a local desktop inventory management system to track a massive variety of products (phones, glass protectors, branded accessories from 8+ brands, non-branded accessories, tablet accessories, phone cases, etc.). The system must handle **add, organize, search, update (buy/sell), and record-keeping** across 130+ product types with varying attributes. The database will be Supabase (cloud PostgreSQL) to protect against data loss from system failure. Built in Python with a professional UI, developed on Linux but must later deploy on Windows.

### Key Decisions
- **No authentication** - App opens directly, single-user system
- **Online-only** - All data reads/writes go directly to Supabase (no offline/local cache)
- **Simple transaction recording** - Record product, quantity, price, date, optional customer name (no invoicing)
- **Modern Dark theme** - Dark background with accent colors for professional, eye-friendly look

---

## 1. Technology Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| **Language** | Python 3.11+ | As requested |
| **UI Framework** | PySide6 (Qt6) | Professional look, cross-platform (Linux+Windows), powerful table/form widgets, sidebar navigation, great for data-heavy apps |
| **Database** | Supabase (cloud PostgreSQL) - online only | All data goes directly to Supabase for safety; requires internet connection |
| **DB Client** | `supabase-py` | Official Python client for Supabase REST API |
| **Packaging** | PyInstaller | For Windows `.exe` deployment later |
| **Styling** | Qt Stylesheets (QSS) | Modern dark theme with accent colors |

### Dependencies (requirements.txt)
```
PySide6>=6.6.0
supabase>=2.0.0
python-dotenv>=1.0.0
```

---

## 2. Project Structure

```
umers_project/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── .env                             # Supabase credentials (gitignored)
├── IMPLEMENTATION_PLAN.md           # This file
├── src/
│   ├── __init__.py
│   ├── config.py                    # App settings, Supabase URL/Key
│   ├── database/
│   │   ├── __init__.py
│   │   ├── supabase_client.py       # Supabase connection singleton
│   │   ├── schema.sql               # SQL DDL for all tables
│   │   ├── seed_data.py             # Pre-populate categories, brands, product types
│   │   ├── repository.py            # Abstract repository interface
│   │   └── supabase_repository.py   # Supabase implementation of repository
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py               # Product dataclass
│   │   ├── category.py              # Category/Subcategory dataclasses
│   │   ├── transaction.py           # Buy/Sell transaction dataclass
│   │   └── attribute.py             # Dynamic attribute definitions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── inventory_service.py     # Business logic for inventory CRUD
│   │   ├── transaction_service.py   # Buy/sell recording logic
│   │   └── search_service.py        # Search and filtering logic
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py           # Main window with sidebar + stacked pages
│   │   ├── theme.py                 # QSS stylesheet / colors / fonts
│   │   ├── pages/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard_page.py    # Overview / summary stats
│   │   │   ├── phones_page.py       # Phones inventory (used, box pack, keypad)
│   │   │   ├── glass_protectors_page.py
│   │   │   ├── branded_accessories_page.py  # Ronin, Space, Login, etc.
│   │   │   ├── accessories_page.py  # Non-branded accessories
│   │   │   ├── cases_page.py        # Phone cases (TPU, branded, local)
│   │   │   ├── tablets_page.py      # Tablets & tablet accessories
│   │   │   ├── lens_page.py         # Camera lens
│   │   │   ├── transactions_page.py # Buy/sell history
│   │   │   └── search_page.py       # Global search results
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── dynamic_form.py      # Auto-generates form fields from attribute definitions
│   │       ├── product_table.py     # Reusable sortable/filterable table widget
│   │       ├── search_bar.py        # Global search bar component
│   │       ├── filter_panel.py      # Category/brand/type filters
│   │       └── transaction_dialog.py # Buy/Sell recording dialog
│   └── utils/
│       ├── __init__.py
│       └── helpers.py               # Formatting, validation helpers
└── assets/
    └── styles/
        └── app.qss                  # Qt stylesheet file
```

**Total files: ~35 Python files + SQL + QSS + config**

---

## 3. Database Schema (Supabase PostgreSQL)

The key design challenge is handling 130+ product types with different attributes (a phone has IMEI/condition/box/charger, a glass protector has brand/type/privacy-or-clear, a power bank has mAh/wattage/connector).

**Solution: Entity-Attribute-Value (EAV) pattern** with a 3-level category hierarchy + dynamic attributes stored as JSONB.

### Table 1: `categories` (Top-level grouping - 7 rows)
| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | Auto-generated |
| name | TEXT UNIQUE | "Phones", "Glass Protectors", "Branded Accessories", "Camera Lens", "Accessories", "Phone Cases", "Tablet Accessories" |
| display_order | INT | Controls sidebar order |

### Table 2: `subcategories` (Second level - ~25 rows)
| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| category_id | UUID FK → categories | Parent category |
| name | TEXT | "Used Phones", "Ronin", "iPhone Glass", "TPU Bumper", etc. |
| display_order | INT | |

### Table 3: `product_types` (Third level - ~130 rows)
| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| subcategory_id | UUID FK → subcategories | Parent subcategory |
| name | TEXT | "Power Bank", "Ear Buds", "OG Glass", "Youksh Privacy", etc. |
| display_order | INT | |

### Table 4: `attribute_definitions` (Dynamic form fields per product type)
| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| product_type_id | UUID FK → product_types | Which product type this belongs to |
| name | TEXT | Machine name: "wattage", "connector_type", "has_box" |
| label | TEXT | Display label: "Wattage (W)", "Connector Type" |
| field_type | TEXT | "text", "number", "boolean", "select" |
| options | JSONB | For select fields: `["C to C", "USB to C", "USB to Lightning"]` |
| is_required | BOOLEAN | Whether field is mandatory |
| display_order | INT | Order in the form |

### Table 5: `products` (Actual inventory items)
| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| product_type_id | UUID FK → product_types | What type of product |
| name | TEXT | Display name (auto-generated or user-provided) |
| brand | TEXT | Brand name (nullable for non-branded items) |
| model | TEXT | Model name/number (nullable) |
| purchase_price | DECIMAL | Cost price in PKR |
| sale_price | DECIMAL | Selling price in PKR |
| quantity | INT | Current stock count |
| status | TEXT | "in_stock", "sold", "claimed" |
| attributes | JSONB | Dynamic key-value pairs: `{"wattage": 20, "connector_type": "C to C"}` |
| notes | TEXT | Free-form notes |
| created_at | TIMESTAMPTZ | Auto-set |
| updated_at | TIMESTAMPTZ | Auto-updated |

### Table 6: `transactions` (Buy/Sell records)
| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| product_id | UUID FK → products | Which product |
| type | TEXT | "purchase" or "sale" |
| quantity | INT | How many units |
| unit_price | DECIMAL | Price per unit at time of transaction |
| total_price | DECIMAL | quantity × unit_price |
| customer_info | TEXT | Optional buyer/seller name |
| notes | TEXT | Optional notes |
| created_at | TIMESTAMPTZ | Transaction date |

### Table 7: `phone_details` (Specialized fields for phones only)
| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| product_id | UUID FK → products | Links to the phone in products table |
| imei | TEXT UNIQUE | IMEI number |
| phone_type | TEXT | "used", "box_pack", "keypad" |
| has_box | BOOLEAN | Does it come with box? |
| has_charger | BOOLEAN | Does it come with charger? |
| keypad_type | TEXT | "keys_only" or "keypad_touchscreen" (nullable, only for keypad phones) |
| is_claimed | BOOLEAN | Has customer claimed it? (keypad phones only) |
| claim_reason | TEXT | Reason for claim (nullable) |
| condition | TEXT | "excellent", "good", "fair", "poor" |
| storage_gb | INT | Storage capacity |
| ram_gb | INT | RAM |
| color | TEXT | Phone color |

### How It Works Together (Example)

**Adding a Ronin Power Bank:**
1. Category: "Branded Accessories" → Subcategory: "Ronin" → Product Type: "Power Bank"
2. System loads attribute_definitions for "Ronin > Power Bank": `[wattage (number), mah_capacity (number), connector_type (select), is_wireless (boolean)]`
3. Dynamic form renders these 4 fields
4. User fills: wattage=20, mah=10000, connector="USB to C", wireless=false
5. Saved to products.attributes as: `{"wattage": 20, "mah_capacity": 10000, "connector_type": "USB to C", "is_wireless": false}`

**Adding a Used Phone:**
1. Category: "Phones" → Subcategory: "Used Phones" → Product Type: "Used Phone"
2. Regular product form + specialized phone_details form (IMEI, box, charger, condition, etc.)

---

## 4. UI Design

### Theme: Modern Dark
- **Background**: Dark charcoal (#1e1e2e)
- **Sidebar**: Slightly darker (#181825)
- **Cards/Panels**: Medium dark (#313244)
- **Accent color**: Blue (#89b4fa) for buttons, highlights
- **Text**: Light gray (#cdd6f4)
- **Success**: Green (#a6e3a1)
- **Warning**: Yellow (#f9e2af)
- **Danger**: Red (#f38ba8)

### Main Window Layout
```
┌──────────────────────────────────────────────────────────────┐
│  [ Search all products...                              ]     │
├─────────────┬────────────────────────────────────────────────┤
│             │                                                │
│  SIDEBAR    │            CONTENT AREA                        │
│  (dark)     │                                                │
│             │  ┌──────────────────────────────────────────┐  │
│  Dashboard  │  │  Page Title        [+ Add New] [Filters] │  │
│  ─────────  │  ├──────────────────────────────────────────┤  │
│  Phones     │  │                                          │  │
│  Glass      │  │  ┌──────┬───────┬─────┬─────┬────────┐  │  │
│  ─────────  │  │  │ Name │ Type  │ Qty │Price│ Action │  │  │
│  Ronin      │  │  ├──────┼───────┼─────┼─────┼────────┤  │  │
│  Space      │  │  │ ...  │ ...   │ ... │ ... │Edit|Del│  │  │
│  Login      │  │  │ ...  │ ...   │ ... │ ... │Edit|Del│  │  │
│  Audionic   │  │  │ ...  │ ...   │ ... │ ... │Edit|Del│  │  │
│  Cherry     │  │  └──────┴───────┴─────┴─────┴────────┘  │  │
│  Faster     │  │                                          │  │
│  Orimo      │  │  Page: [1] [2] [3] ... [Next]            │  │
│  Taar       │  └──────────────────────────────────────────┘  │
│  ─────────  │                                                │
│  Lens       │                                                │
│  Accessories│                                                │
│  Cases      │                                                │
│  Tablets    │                                                │
│  ─────────  │                                                │
│  Transactions│                                               │
│             │                                                │
└─────────────┴────────────────────────────────────────────────┘
```

### Key UI Pages

1. **Dashboard Page**
   - Summary cards: Total Stock Value, Total Items, Today's Sales, Today's Purchases, Low Stock Alerts
   - Recent transactions list

2. **Category Pages** (Phones, Glass, each Brand, Accessories, Cases, Tablets, Lens)
   - Product table with sortable columns
   - Filter panel (by subcategory, product type, status)
   - Action buttons: Add New, Buy (record purchase), Sell (record sale)
   - Inline edit/delete per row

3. **Add/Edit Product Dialog** (popup)
   - Step 1: Select Category → Subcategory → Product Type (cascading dropdowns)
   - Step 2: Dynamic form auto-generates fields based on attribute_definitions
   - Step 3: Common fields (name, purchase price, sale price, quantity, notes)
   - For phones: Additional phone_details section (IMEI, box, charger, condition, etc.)

4. **Buy/Sell Transaction Dialog** (popup)
   - Product selector (searchable dropdown)
   - Quantity input
   - Unit price input
   - Optional customer name
   - Optional notes
   - Auto-calculates total

5. **Transactions Page**
   - Table of all transactions with columns: Date, Product, Type (Buy/Sell), Qty, Price, Customer
   - Date range filter
   - Filter by type (purchase/sale)

6. **Search Results Page**
   - Triggered by global search bar
   - Shows matching products across ALL categories
   - Each result shows: Name, Category, Brand, Type, Qty, Price

### Dynamic Form System (Key Architecture Decision)

This is the core innovation that makes the system scalable:
- Instead of writing separate forms for each of 130+ product types, we have ONE `DynamicForm` component
- It reads `attribute_definitions` from the database for the selected product type
- It auto-generates form fields based on `field_type`:
  - `"text"` → QLineEdit
  - `"number"` → QSpinBox / QDoubleSpinBox
  - `"boolean"` → QCheckBox
  - `"select"` → QComboBox (populated from `options` JSON)
- Adding a new product type in the future only requires adding database rows, not code changes

---

## 5. Seed Data Summary

All of this data gets pre-populated when the app first runs:

### Categories (7)
1. Phones
2. Glass Protectors
3. Branded Accessories
4. Camera Lens
5. Accessories (non-branded)
6. Phone Cases
7. Tablet Accessories

### Subcategories (~25)
- **Phones**: Used Phones, Box Pack Phones, Keypad Phones
- **Glass Protectors**: iPhone Glass, Android Glass
- **Branded Accessories**: Ronin, Space, Login, Audionic, Cherry, Faster, Orimo, Taar
- **Camera Lens**: iPhone Lens, Android Lens
- **Accessories**: Non-branded Accessories
- **Phone Cases**: TPU Bumper Case, Original Branded Case, Local Branded Case
- **Tablet Accessories**: iPad Accessories, Samsung Tablet Accessories, General Accessories

### Product Types (~130) - Full Breakdown

**Ronin (13 types):** Power Bank, Ear Buds, Neckband, Charger, 20W Adapter, Speaker, Sound Bar, 2-in-1 Cable, 3-in-1 Cable, Car Charger, Gaming Handfree, Wireless Headphone, Cables, Smart Watch

**Space (15 types):** Power Bank, 3-in-1 Wireless Power Bank, Wireless Power Bank, Neckband, Charger, Sound Bar, Ear Buds, 3 Amp Charger, Aux Cable, USB Cable, Handfree, Car Charger, 3-in-1 Cable, Headphone, Smart Watch

**Login (19 types):** 12W Charger, 20W Charger, 18W Charger, Silica Gel Cable, 35W Type-C Cable, 22.5W Cable, C-to-C Cable, C-to-Lightning Cable, Handfree (Type-C/AUX), Handfree (iPhone), Car Charger, Speaker, Headphone, Gaming Headphone, Sound Bar, Power Bank, 65W Power Bank, Wireless Power Bank, Smart Watch

**Audionic (6 types):** Power Bank, Ear Buds, Handfree, Car Charger, Charging Cable, Wireless Speaker

**Cherry (2 types):** Handfree, Charging Cable

**Faster (15 types):** Power Bank, Wireless Power Bank, Handfree, Car Charger, C-type Charger, B-type Charger, 3-in-1 Cable, 2-in-1 Cable, 2m Cable, Jumbo Speaker, Sound Bar, Wireless Headphone, Bike Mobile Charger, C-to-C Cable, Lightning-to-Lightning Cable

**Orimo (6 types):** Handfree, Lightning Cable, 2m Cable, C-to-C Cable, Speaker, Neckband

**Taar (4 types):** C-to-Lightning Cable, USB Cable, 12W Charger, 18W Charger

**iPhone Glass (9 types):** OG Glass, Youksh Privacy, Youksh Clear, Flayer, Kuzoom Privacy, Kuzoom Clear, Coblu Privacy, Coblu Clear, Blue Shark, Soqoo, Borderless Glass, Milake Privacy

**Android Glass (2 types):** OG Glass, 9D Glass

**Non-branded Accessories (61+ types):** All items from the requirements doc (adapters, cables, converters, wireless chargers, mikes, selfie sticks, stands, covers, etc.)

**Phone Cases (6 types):** TPU Bumper (iPhone), TPU Bumper (Android), Original Branded (iPhone), Original Branded (Android), Local Branded, Polo Logo

**Tablet Accessories (10 types):** iPad Back Cover, iPad Glass, Samsung Tablet Cover, Samsung Tablet Glass, Universal Glass, Memory Card, USB Drive, Laptop Power Cable, Computer Power Cable, Laptop Cooling Pad

**Camera Lens (2 types):** Blue Shark iPhone Lens, Blue Shark Android Lens

### Attribute Definitions (examples per product type)
| Product Type | Attributes |
|-------------|------------|
| Power Bank | wattage (number), mah_capacity (number), connector_type (select), is_wireless (boolean), charging_type (select: PD/Simple) |
| Charger | wattage (number), connector_type (select), cable_included (boolean) |
| Ear Buds / Neckband | connectivity (select: wireless/wired) |
| Handfree | connector_type (select: AUX/Type-C/Lightning), variant (text) |
| Cable | from_type (select), to_type (select), length (select: 1m/2m), material (select: Simple/Silica Gel) |
| Glass Protector | glass_type (select: Privacy/Clear), compatible_models (text), glass_variant (select: Simple/Polish/9D) |
| Phone Case | case_material (select: TPU/Hard/MagSafe), color (text), compatible_model (text) |
| Used Phone | (uses phone_details table instead) |
| Sound Bar | wattage (number) |
| Smart Watch | connectivity (select: Bluetooth/WiFi) |
| Speaker | speaker_size (select: Small/Large/Jumbo), is_wireless (boolean) |
| Car Charger | wattage (number), connector_type (select), cable_included (boolean) |
| Memory Card / USB | storage_gb (select: 4/8/16/32/64/128/256), brand_type (select: SanDisk/Samsung Copy) |
| Converter | from_type (select), to_type (select) |

---

## 6. Implementation Phases

### Phase 1: Foundation (Core Infrastructure)
**Files to create:**
- `main.py` - App entry point
- `requirements.txt` - Dependencies
- `.env` - Supabase URL and anon key
- `src/config.py` - Load env vars, app settings
- `src/database/supabase_client.py` - Supabase connection singleton
- `src/database/schema.sql` - All 7 tables DDL
- `src/database/repository.py` - Abstract interface (get, list, create, update, delete for each entity)
- `src/database/supabase_repository.py` - Supabase implementation
- `src/models/*.py` - All dataclasses (Product, Category, Subcategory, ProductType, AttributeDefinition, Transaction, PhoneDetails)
- `src/database/seed_data.py` - Seed ALL categories, subcategories, product types, and attribute definitions

**Outcome:** Database connected, all tables created in Supabase, seed data populated, CRUD operations working via Python

### Phase 2: UI Shell + Navigation + Dashboard
**Files to create:**
- `src/ui/main_window.py` - Main window (sidebar + QStackedWidget + search bar)
- `src/ui/theme.py` - Dark theme colors + QSS generation
- `assets/styles/app.qss` - Base stylesheet
- `src/ui/components/search_bar.py` - Global search bar widget
- `src/ui/pages/dashboard_page.py` - Summary cards + recent activity

**Outcome:** App launches with dark theme, sidebar navigation works, dashboard shows stock summary

### Phase 3: Product Management (Core Feature)
**Files to create:**
- `src/ui/components/dynamic_form.py` - Auto-generating form based on attribute_definitions
- `src/ui/components/product_table.py` - Reusable sortable/filterable QTableWidget
- `src/ui/components/filter_panel.py` - Filters (subcategory, product type, status dropdowns)
- `src/services/inventory_service.py` - Business logic layer
- `src/ui/pages/phones_page.py` - Phones with phone_details integration
- `src/ui/pages/branded_accessories_page.py` - Generic page for all 8 brands
- `src/ui/pages/glass_protectors_page.py`
- `src/ui/pages/accessories_page.py`
- `src/ui/pages/cases_page.py`
- `src/ui/pages/tablets_page.py`
- `src/ui/pages/lens_page.py`

**Outcome:** Can add, view, edit, delete products in ALL categories. Dynamic forms auto-generate correct fields per product type.

### Phase 4: Buy/Sell Transactions
**Files to create:**
- `src/ui/components/transaction_dialog.py` - Buy/Sell popup dialog
- `src/ui/pages/transactions_page.py` - Transaction history with date filters
- `src/services/transaction_service.py` - Record transactions, auto-update stock quantities

**Outcome:** Can record purchases and sales. Stock quantities auto-update. Full transaction history with filtering.

### Phase 5: Search + Polish
**Files to create:**
- `src/services/search_service.py` - Search across products table + JSONB attributes
- `src/ui/pages/search_page.py` - Global search results page
- `src/utils/helpers.py` - Price formatting, input validation, etc.

**Outcome:** Global search works across all products. UI polished. Edge cases handled.

---

## 7. Verification / Testing Plan

After each phase, verify:

1. **Phase 1 check:** Run seed script, verify all tables populated in Supabase dashboard
2. **Phase 2 check:** `python main.py` opens window with dark theme, sidebar navigates between pages
3. **Phase 3 checks:**
   - Add a used phone with IMEI, brand, model, box/charger → appears in Phones table
   - Add a Ronin Power Bank → dynamic form shows wattage, mAh, connector fields
   - Add a Youksh Privacy Glass → form shows glass_type=Privacy, compatible models field
   - Edit a product → changes saved to Supabase
   - Delete a product → removed from table and Supabase
4. **Phase 4 checks:**
   - Record purchase of 10 Ronin Power Banks → stock shows 10
   - Record sale of 3 → stock shows 7
   - Transaction history page shows both records with dates
5. **Phase 5 checks:**
   - Search "Ronin" → shows all Ronin products
   - Search "power bank" → shows power banks from all brands
   - Search "privacy" → shows all privacy glass protectors

---

## 8. Future Scalability

This architecture supports future additions without code changes:
- **New brand?** → Add rows to subcategories + product_types + attribute_definitions
- **New product type?** → Add rows to product_types + attribute_definitions
- **New attribute?** → Add row to attribute_definitions
- **Windows deployment?** → Run PyInstaller to create .exe (PySide6 is cross-platform)
- **Multi-user later?** → Supabase supports Row Level Security (RLS) when ready
- **Invoice generation later?** → Add new service + page without touching existing code
