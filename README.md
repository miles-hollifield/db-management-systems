# CSC440 Project 1 - Complete Final Entity Structure

## Team Members
 * Miles Hollifield (mfhollif)
 *  Claire Jeffries (cmjeffri)
 *  Abhi Pai (apai5)

## User Management System

```
USER
- user_id (PK, INT, AUTO_INCREMENT)
- username (VARCHAR(50), NOT NULL, UNIQUE)
- password_hash (VARCHAR(255), NOT NULL)
- role (ENUM('MANUFACTURER', 'SUPPLIER', 'VIEWER'), NOT NULL)
- created_date (DATE, NOT NULL, DEFAULT CURRENT_DATE)

MANUFACTURER
- manufacturer_id (PK, INT, AUTO_INCREMENT)
- user_id (FK → USER, NOT NULL, UNIQUE)
- name (VARCHAR(255), NOT NULL)

SUPPLIER  
- supplier_id (PK, INT, AUTO_INCREMENT)
- user_id (FK → USER, NOT NULL, UNIQUE)
- name (VARCHAR(255), NOT NULL)
```
*Note: VIEWER role requires no additional entity - read-only access*

## Core Domain Entities

```
CATEGORY
- category_id (PK, INT, AUTO_INCREMENT) 
- name (VARCHAR(100), NOT NULL, UNIQUE)

PRODUCT
- product_id (PK, INT, AUTO_INCREMENT)
- name (VARCHAR(255), NOT NULL)
- category_id (FK → CATEGORY, NOT NULL)
- manufacturer_id (FK → MANUFACTURER, NOT NULL)
- standard_batch_size (INT, NOT NULL)

INGREDIENT -- Supplier-owned ingredient definitions
- ingredient_id (PK, INT, AUTO_INCREMENT)
- supplier_id (FK → SUPPLIER, NOT NULL) -- Who owns/defines this ingredient
- name (VARCHAR(255), NOT NULL)
- type (ENUM('ATOMIC', 'COMPOUND'), NOT NULL)
```

## Recipe Management (Versioned)

```
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
- quantity_required (DECIMAL(10,3), NOT NULL) -- ounces per unit of product
-- Composite PK: (plan_id, ingredient_id)
```

## Supplier Formulations (Pricing & Versioning for Ingredients)

```
FORMULATION
- formulation_id (PK, INT, AUTO_INCREMENT)
- ingredient_id (FK → INGREDIENT, NOT NULL) -- Links to supplier's ingredient
- pack_size (DECIMAL(10,3), NOT NULL) -- units in pack
- unit_price (DECIMAL(10,2), NOT NULL) -- price per pack
- effective_start_date (DATE, NOT NULL)
- effective_end_date (DATE, NULL) -- NULL means currently active
-- UNIQUE(ingredient_id, effective_start_date)
-- CHECK(effective_end_date IS NULL OR effective_end_date > effective_start_date)

FORMULATION_MATERIAL -- Only for compound ingredients
- formulation_id (PK, FK → FORMULATION)
- material_ingredient_id (PK, FK → INGREDIENT) -- References other suppliers' ingredients
- quantity_required (DECIMAL(10,3), NOT NULL) -- ounces of material per unit of compound
-- Composite PK: (formulation_id, material_ingredient_id)
```

## Batch/Lot Tracking

```
INGREDIENT_BATCH
- lot_number (PK, VARCHAR(50)) -- Format: ingredientId-supplierId-batchId
- ingredient_id (FK → INGREDIENT, NOT NULL)
- batch_id (VARCHAR(20), NOT NULL) -- Supplier's internal batch identifier
- quantity (DECIMAL(10,3), NOT NULL) -- ounces on hand (decremented as used)
- cost_per_unit (DECIMAL(10,2), NOT NULL) -- cost per ounce
- expiration_date (DATE, NOT NULL)
- received_date (DATE, NOT NULL, DEFAULT CURRENT_DATE)
-- CHECK(expiration_date >= received_date + INTERVAL 90 DAY)

PRODUCT_BATCH
- lot_number (PK, VARCHAR(50)) -- Format: productId-manufacturerId-batchId
- product_id (FK → PRODUCT, NOT NULL)
- manufacturer_id (FK → MANUFACTURER, NOT NULL)
- plan_id (FK → RECIPE_PLAN, NOT NULL) -- which recipe version was used
- batch_id (VARCHAR(20), NOT NULL) -- Manufacturer's internal batch identifier
- quantity_produced (INT, NOT NULL) -- units produced
- total_cost (DECIMAL(12,2), NOT NULL) -- calculated from consumed ingredients
- per_unit_cost (DECIMAL(10,4), NOT NULL) -- total_cost / quantity_produced
- production_date (DATE, NOT NULL, DEFAULT CURRENT_DATE)

BATCH_CONSUMPTION -- Traceability: which ingredient lots went into which product batches
- product_batch_lot (PK, FK → PRODUCT_BATCH.lot_number)
- ingredient_batch_lot (PK, FK → INGREDIENT_BATCH.lot_number)
- quantity_consumed (DECIMAL(10,3), NOT NULL) -- ounces consumed from this ingredient lot
-- Composite PK: (product_batch_lot, ingredient_batch_lot)
```

## Key Business Rules & Constraints

1. **User-Role Mapping**: Each user has exactly one role; manufacturers and suppliers link to user accounts
2. **Ingredient Ownership**: Suppliers own and define ingredients (same name can exist across suppliers as different ingredient_ids)
3. **One-Level Composition**: Materials in FORMULATION_MATERIAL cannot themselves have materials (enforced by application logic)
4. **Lot Format**: Enforced by triggers (ingredientId-supplierId-batchId for ingredients, productId-manufacturerId-batchId for products)
5. **90-Day Rule**: Ingredient expiration must be ≥ 90 days from received date
6. **Batch Size Multiple**: Product batches must be integer multiples of standard_batch_size
7. **Access Control**: Users can only work with entities they own based on role
8. **Active Formulations**: Selected by date range (no overlapping periods per ingredient)
9. **Active Recipes**: Only one active recipe plan per product at a time

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

This structure properly handles supplier-owned ingredient definitions, user authentication, and complete traceability as specified in the requirements.

# CSC440 Project - Short Report: Modeling Choices and Query Reasoning

## Key Modeling Decisions

**User System**: Implemented separate USER entity with role field linking to MANUFACTURER/SUPPLIER entities. This supports the "Login → Select role" flow in Appendix A while enforcing the "one role per user" constraint.

**Supplier-Owned Ingredients**: INGREDIENT entity includes supplier_id as owner because suppliers "Define/Update Ingredient" per functional requirements. Same ingredient names can exist across different suppliers as distinct entities.

**Versioned Formulations**: Separate FORMULATION entity handles pricing and effective dates while keeping core ingredient definition stable. Supports "versioned formulations" with "non-overlapping effective periods."

**Recipe Versioning**: Used explicit version numbers with is_active flag rather than date-based selection because requirements state "the plan used in production is selected explicitly."

**Lot Number Format**: VARCHAR primary keys with format "ingredientId-supplierId-batchId" enforced by triggers for required traceability.

**Batch Consumption**: Bridge entity BATCH_CONSUMPTION captures "exactly which ingredient lots were consumed" for complete supply chain traceability.

## Query Design Reasoning

**Q1**: Search by ingredient name (case-insensitive) since users likely search "Seasoning Blend" rather than knowing ingredient IDs. Shows all supplier versions with active formulations.

**Q2**: Filters for quantity > 0 and groups by ingredient/supplier for actionable expiry reporting.

**Q3**: Includes manufacturer/supplier names for ownership clarity and aggregates ingredient availability across all batches.

**Q4**: Compares total production to standard batch size for "nearly-out-of-stock" determination as defined in requirements.

**Q5**: Includes nesting violation detection via EXISTS subquery to validate the one-level composition constraint.

**Q6**: Calculates ingredient cost contribution (quantity × unit cost) for complete production cost traceability.

## Constraints Not Captured in E-R Notation

**One-Level Composition**: Materials in compound ingredients cannot themselves have materials (no grandchildren in hierarchy).

**Lot Number Format**: INGREDIENT_BATCH follows "ingredientId-supplierId-batchId"; PRODUCT_BATCH follows "productId-manufacturerId-batchId".

**Non-Overlapping Formulations**: Same ingredient cannot have overlapping effective date ranges.

**90-Day Expiration Rule**: Ingredient expiration must be ≥ received_date + 90 days.

**Role-Entity Mapping**: Users with role='MANUFACTURER' must have MANUFACTURER record; users with role='SUPPLIER' must have SUPPLIER record.

**Active Recipe Constraint**: Only one recipe plan per product can have is_active = TRUE.