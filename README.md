# CSC440 Project - Inventory Management System

**Prepared/Frozen Meals Manufacturer Database Application**

## Team Members
- Miles Hollifield (mfhollif)
- Claire Jeffries (cmjeffri)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Improvements from Deliverable 1](#improvements-from-deliverable-1)
3. [Entity Structure](#entity-structure)
4. [Key Design Decisions](#key-design-decisions)
5. [Implementation Details](#implementation-details)
6. [Business Rules & Constraints](#business-rules--constraints)
7. [Installation & Usage](#installation--usage)

---

## Project Overview

This project implements a comprehensive inventory management system for a prepared/frozen meals manufacturer. The system tracks:
- **Products** (Steak Dinners, Mac & Cheese, Desserts)
- **Ingredients** (Atomic and Compound with one-level nesting)
- **Suppliers** (who define and provide ingredients)
- **Manufacturers** (who create products and manage production)
- **Complete Traceability** (from ingredient lots to finished product batches)
- **Recipe Versioning** (with explicit activation)
- **Cost Tracking** (per-batch and per-unit calculations)

**Technology Stack:**
- Database: MySQL/MariaDB 8.0+
- Application: Python 3.8+ with mysql-connector-python
- Interface: Command-line menu-driven application

---

## Improvements from Deliverable 1

### Schema Changes

**1. Manufacturer ID Data Type Update**
- **Before**: `manufacturer_id INT AUTO_INCREMENT`
- **After**: `manufacturer_id VARCHAR(20)`
- **Reason**: Matches provided sample data format (MFG001, MFG002) and improves lot number readability

**2. Ingredient Batch Enhancement**
- **Added**: `supplier_id INT NOT NULL` (user must provide explicitly)
- **Added**: `manufacturer_id VARCHAR(20) NULL` (distinguishes supplier-created vs manufacturer-received batches)
- **Added**: `on_hand_oz DECIMAL(10,3)` (maintains current inventory automatically via triggers)
- **Reason**: Supports dual-role batch creation and automated inventory tracking

**3. 90-Day Rule Refinement**
- **Before**: CHECK constraint in database on INGREDIENT_BATCH
- **After**: Enforced in application code for manufacturers only
- **Reason**: Suppliers can create batches without restriction; only manufacturers must enforce the 90-day rule on intake

**4. Trigger Logic Updates**
- **Lot Number Generation**: Now accepts user-provided `ingredient_id`, `supplier_id`, and `batch_id` before auto-generating lot number
- **On-Hand Initialization**: Properly initializes `on_hand_oz = quantity` on INSERT instead of circular update
- **Reason**: Fixes implementation issues discovered during testing

### Functional Enhancements

**1. Viewer Role Workflow Correction**
- **Before**: General → Product → Ingredient List
- **After**: General → Product → Product Batch → Ingredient List
- **Reason**: Clarification from project instructions - viewers see ingredients consumed in specific batches, not just recipes

**2. Date Validation**
- All sample data updated for November 2025 with expiration dates in 2026
- Prevents trigger rejections during data loading
- Realistic for current academic term

**3. Password Authentication**
- Simplified username-only authentication (matches project requirements)
- No database-level privileges needed
- Focus on database design and business logic

---

## Entity Structure

### User Management System

```sql
USER
- user_id (PK, INT, AUTO_INCREMENT)
- username (VARCHAR(50), NOT NULL, UNIQUE)
- password_hash (VARCHAR(255), NOT NULL)
- role (ENUM('MANUFACTURER', 'SUPPLIER', 'VIEWER'), NOT NULL)
- created_date (DATE, NOT NULL, DEFAULT CURRENT_DATE)

MANUFACTURER
- manufacturer_id (VARCHAR(20), PK)  -- Changed from INT
- user_id (FK → USER, NOT NULL, UNIQUE)
- name (VARCHAR(255), NOT NULL)

SUPPLIER  
- supplier_id (INT, PK, AUTO_INCREMENT)
- user_id (FK → USER, NOT NULL, UNIQUE)
- name (VARCHAR(255), NOT NULL)
```

### Core Domain Entities

```sql
CATEGORY
- category_id (PK, INT, AUTO_INCREMENT) 
- name (VARCHAR(100), NOT NULL, UNIQUE)

PRODUCT
- product_id (PK, INT, AUTO_INCREMENT)
- name (VARCHAR(255), NOT NULL)
- category_id (FK → CATEGORY, NOT NULL)
- manufacturer_id (FK → MANUFACTURER, NOT NULL, VARCHAR(20))  -- Updated
- standard_batch_size (INT, NOT NULL)

INGREDIENT -- Supplier-owned ingredient definitions
- ingredient_id (PK, INT, AUTO_INCREMENT)
- supplier_id (FK → SUPPLIER, NOT NULL)
- name (VARCHAR(255), NOT NULL)
- type (ENUM('ATOMIC', 'COMPOUND'), NOT NULL)
```

### Recipe Management (Versioned)

```sql
RECIPE_PLAN
- plan_id (PK, INT, AUTO_INCREMENT)
- product_id (FK → PRODUCT, NOT NULL)
- version_number (INT, NOT NULL)
- created_date (DATE, NOT NULL, DEFAULT CURRENT_DATE)
- is_active (BOOLEAN, NOT NULL, DEFAULT FALSE)
-- UNIQUE(product_id, version_number)

RECIPE_INGREDIENT  
- plan_id (PK, FK → RECIPE_PLAN)
- ingredient_id (PK, FK → INGREDIENT)
- quantity_required (DECIMAL(10,3), NOT NULL)
-- Composite PK: (plan_id, ingredient_id)
```

### Supplier Formulations

```sql
FORMULATION
- formulation_id (PK, INT, AUTO_INCREMENT)
- ingredient_id (FK → INGREDIENT, NOT NULL)
- pack_size (DECIMAL(10,3), NOT NULL)
- unit_price (DECIMAL(10,2), NOT NULL)
- effective_start_date (DATE, NOT NULL)
- effective_end_date (DATE, NULL)
-- UNIQUE(ingredient_id, effective_start_date)

FORMULATION_MATERIAL
- formulation_id (PK, FK → FORMULATION)
- material_ingredient_id (PK, FK → INGREDIENT)
- quantity_required (DECIMAL(10,3), NOT NULL)
-- Composite PK: (formulation_id, material_ingredient_id)
```

### Batch/Lot Tracking

```sql
INGREDIENT_BATCH
- lot_number (PK, VARCHAR(50))  -- Format: ingredientId-supplierId-batchId
- ingredient_id (FK → INGREDIENT, NOT NULL)
- supplier_id (INT, NOT NULL)  -- New: user must provide
- manufacturer_id (VARCHAR(20), NULL)  -- New: NULL for supplier-created batches
- batch_id (VARCHAR(20), NOT NULL)
- quantity (DECIMAL(10,3), NOT NULL)
- cost_per_unit (DECIMAL(10,2), NOT NULL)
- expiration_date (DATE, NOT NULL)
- received_date (DATE, NOT NULL, DEFAULT CURRENT_DATE)
- on_hand_oz (DECIMAL(10,3), DEFAULT 0)  -- New: auto-maintained by triggers

PRODUCT_BATCH
- lot_number (PK, VARCHAR(50))  -- Format: productId-manufacturerId-batchId
- product_id (FK → PRODUCT, NOT NULL)
- manufacturer_id (FK → MANUFACTURER, NOT NULL, VARCHAR(20))  -- Updated
- plan_id (FK → RECIPE_PLAN, NOT NULL)
- batch_id (VARCHAR(20), NOT NULL)
- quantity_produced (INT, NOT NULL)
- total_cost (DECIMAL(12,2), NOT NULL)
- per_unit_cost (DECIMAL(10,4), NOT NULL)
- production_date (DATE, NOT NULL, DEFAULT CURRENT_DATE)

BATCH_CONSUMPTION
- product_batch_lot (PK, FK → PRODUCT_BATCH.lot_number)
- ingredient_batch_lot (PK, FK → INGREDIENT_BATCH.lot_number)
- quantity_consumed (DECIMAL(10,3), NOT NULL)
-- Composite PK: (product_batch_lot, ingredient_batch_lot)
```

---

## Key Design Decisions

### 1. User Authentication System
**Decision**: Separate USER entity with role-based mapping to MANUFACTURER/SUPPLIER entities.

**Reasoning**: Supports the "Login → Select role" flow while enforcing "one role per user" constraint. VIEWER role requires no additional entity (read-only access).

### 2. Supplier Ownership of Ingredients
**Decision**: INGREDIENT entity includes supplier_id as owner.

**Reasoning**: Suppliers "Define/Update Ingredient" per functional requirements. Multiple suppliers can create ingredients with the same name as distinct entities.

**Impact**: Enables business scenario where "Supplier A's Seasoning Blend" and "Supplier B's Seasoning Blend" are completely different ingredients.

### 3. Formulation as Pricing/Versioning Layer
**Decision**: Separate FORMULATION entity for pricing and temporal validity.

**Reasoning**: Suppliers version pricing/packaging over time while maintaining core ingredient definition. Supports non-overlapping effective periods.

### 4. Recipe Plan Versioning
**Decision**: Explicit versioning with `is_active` flag.

**Reasoning**: Requirements state "the plan used in production is selected explicitly" - manufacturers manually choose which version to use.

### 5. Lot Number Strategy
**Decision**: VARCHAR primary keys with trigger-enforced format.

**Reasoning**: Maintains required traceability format while allowing flexible batch identifiers. Prioritizes readability and audit trail over query performance.

### 6. Dual-Role Batch Creation
**Decision**: Both suppliers and manufacturers can create ingredient batches.

**Reasoning**: Clarification from project instructions - suppliers create batches (manufacturer_id = NULL), manufacturers receive/intake batches (manufacturer_id set).

---

## Implementation Details

### Database Features

**Triggers (4 total):**
1. `trg_compute_ingredient_lot_number` - Auto-generates lot numbers on INSERT
2. `trg_initialize_on_hand` - Sets on_hand_oz = quantity on new batches
3. `trg_prevent_expired_consumption` - Blocks consumption of expired lots
4. `trg_decrement_on_hand` - Automatically updates inventory on consumption

**Stored Procedures (1 total):**
1. `RecordProductionBatch` - Creates product batch, consumes ingredient lots, calculates costs

**Views (2 total):**
1. `vw_active_formulations` - Current supplier formulations
2. `vw_flattened_product_bom` - Product recipes with ingredients sorted by quantity

**Required Queries (5 total):**
1. List all products and their categories
2. Last batch ingredients for Steak Dinner (100) by MFG001
3. Suppliers and total spent for MFG002
4. Manufacturers NOT supplied by Supplier B (21)
5. Unit cost for product lot 100-MFG001-B0901

### Application Features

**Role-Based Menus:**
- **Manufacturer**: Create products, recipes, batches; receive ingredients; run reports
- **Supplier**: Define ingredients, create formulations, create batches
- **Viewer**: Browse products, generate ingredient lists (Product → Batch → Ingredients)

**Reports (Manufacturer only):**
- On-hand inventory by lot
- Nearly-out-of-stock products
- Almost-expired ingredient lots (within 10 days)
- Batch cost summary

**Validation:**
- 90-day expiration rule (manufacturer intake only)
- Batch size multiples for production
- Sufficient ingredient quantities before production
- Non-negative inventory balances
- Lot number format compliance

---

## Business Rules & Constraints

### Database-Enforced Constraints
- Foreign key integrity with appropriate CASCADE/RESTRICT
- CHECK constraints for positive values
- UNIQUE constraints for lot numbers and version combinations
- Triggers for lot number format and inventory management

### Application-Enforced Constraints
- One-level composition for compound ingredients
- Single active recipe per product
- 90-day minimum expiration (manufacturer level)
- Batch size multiple validation
- Role-based access control

### Business Logic
- Suppliers own ingredient definitions
- Manufacturers own products
- Complete lot traceability from ingredients to finished goods
- Cost calculation from actual consumed lots
- Formulation versioning with date-based validity

---

## Installation & Usage

### Prerequisites
```bash
# Required software
- Python 3.8+
- MySQL/MariaDB 8.0+
- pip (Python package manager)
```

### Installation Steps

1. **Clone/Download Project Files**
   ```
   - schema.sql
   - data.sql
   - main.py
   - database_connection.py
   - manufacturer_menu.py
   - supplier_menu.py
   - viewer_menu.py
   - query_executor.py
   - requirements.txt
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Database**
   - Open MySQL Workbench
   - Execute `schema.sql` (creates all tables, triggers, procedures, views)
   - Execute `data.sql` (loads sample data)

4. **Configure Connection**
   
   Create `.env` file in project root:
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password_here
   DB_NAME=inventory_db
   ```

5. **Run Application**
   ```bash
   python main.py
   ```

### Sample User Accounts

| Role | Username | Manufacturer/Supplier |
|------|----------|----------------------|
| Manufacturer | jsmith | Manufacturer 1 (MFG001) |
| Manufacturer | bpsi | Manufacturer 2 (MFG002) |
| Supplier | alee | Supplier A (ID: 20) |
| Supplier | jdoe | Supplier B (ID: 21) |
| Viewer | bjohnson | N/A (read-only) |

**Note**: Simplified authentication (username only) per project requirements.

---

## Key Relationships Summary

- **USER** → **MANUFACTURER/SUPPLIER** (1:1, role-based)
- **SUPPLIER** → **INGREDIENT** (1:many, ownership)
- **MANUFACTURER** → **PRODUCT** (1:many, ownership)
- **PRODUCT** → **RECIPE_PLAN** (1:many, versioned)
- **INGREDIENT** → **FORMULATION** (1:many, versioned pricing)
- **FORMULATION** → **FORMULATION_MATERIAL** (1:many, compound composition)
- **INGREDIENT** → **INGREDIENT_BATCH** (1:many, physical lots)
- **PRODUCT** → **PRODUCT_BATCH** (1:many, production lots)
- **PRODUCT_BATCH** ↔ **INGREDIENT_BATCH** (many:many via BATCH_CONSUMPTION, traceability)

---

## Contact

For questions or issues:
- Miles Hollifield: mfhollif@ncsu.edu
- Claire Jeffries: cmjeffri@ncsu.edu

---

**Last Updated**: November 2025 for CSC440 Deliverable 2