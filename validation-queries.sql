-- CSC440 Project 1: Updated Initial Validation Queries (Q1-Q6)
-- These queries validate the updated database model with supplier-owned ingredients

-- Q1: Ingredient Suppliers & Prices
-- For a given ingredient, list all suppliers, current active formulation version, 
-- unit price, and pack size.

SELECT 
    i.ingredient_id,
    i.name AS ingredient_name,
    s.supplier_id,
    s.name AS supplier_name,
    f.formulation_id,
    f.pack_size,
    f.unit_price,
    f.effective_start_date,
    f.effective_end_date
FROM INGREDIENT i
JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
JOIN FORMULATION f ON i.ingredient_id = f.ingredient_id
WHERE i.ingredient_id = ? -- Parameter: specific ingredient ID
  AND (f.effective_end_date IS NULL OR f.effective_end_date >= CURRENT_DATE)
  AND f.effective_start_date <= CURRENT_DATE
ORDER BY s.name, f.effective_start_date DESC;

-- Alternative Q1: For a given ingredient NAME, show all supplier versions
-- (Since same ingredient names can exist across suppliers)

SELECT 
    i.ingredient_id,
    i.name AS ingredient_name,
    s.supplier_id,
    s.name AS supplier_name,
    f.formulation_id,
    f.pack_size,
    f.unit_price,
    f.effective_start_date,
    f.effective_end_date
FROM INGREDIENT i
JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
JOIN FORMULATION f ON i.ingredient_id = f.ingredient_id
WHERE LOWER(i.name) = LOWER(?) -- Parameter: ingredient name (case-insensitive)
  AND (f.effective_end_date IS NULL OR f.effective_end_date >= CURRENT_DATE)
  AND f.effective_start_date <= CURRENT_DATE
ORDER BY s.name, f.effective_start_date DESC;

-- Q2: Expiring Soon
-- List all ingredient lots expiring within the next N days, 
-- grouped by ingredient and supplier.

SELECT 
    i.ingredient_id,
    i.name AS ingredient_name,
    s.supplier_id,
    s.name AS supplier_name,
    ib.lot_number,
    ib.quantity,
    ib.expiration_date,
    DATEDIFF(ib.expiration_date, CURRENT_DATE) AS days_until_expiry
FROM INGREDIENT_BATCH ib
JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
WHERE ib.expiration_date <= DATE_ADD(CURRENT_DATE, INTERVAL ? DAY) -- Parameter: N days
  AND ib.expiration_date >= CURRENT_DATE
  AND ib.quantity > 0
ORDER BY i.name, s.name, ib.expiration_date;

-- Q3: Product Recipe Validation
-- For a given product, show its active recipe with all required ingredients
-- and verify ingredient availability across all suppliers.

SELECT 
    p.product_id,
    p.name AS product_name,
    m.name AS manufacturer_name,
    rp.plan_id,
    rp.version_number,
    i.ingredient_id,
    i.name AS ingredient_name,
    s.name AS ingredient_supplier,
    i.type AS ingredient_type,
    ri.quantity_required,
    COALESCE(SUM(ib.quantity), 0) AS total_available
FROM PRODUCT p
JOIN MANUFACTURER m ON p.manufacturer_id = m.manufacturer_id
JOIN RECIPE_PLAN rp ON p.product_id = rp.product_id
JOIN RECIPE_INGREDIENT ri ON rp.plan_id = ri.plan_id
JOIN INGREDIENT i ON ri.ingredient_id = i.ingredient_id
JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
LEFT JOIN INGREDIENT_BATCH ib ON i.ingredient_id = ib.ingredient_id 
    AND ib.quantity > 0 
    AND ib.expiration_date > CURRENT_DATE
WHERE p.product_id = ? -- Parameter: specific product ID
  AND rp.is_active = TRUE
GROUP BY p.product_id, p.name, m.name, rp.plan_id, rp.version_number, 
         i.ingredient_id, i.name, s.name, i.type, ri.quantity_required
ORDER BY ri.quantity_required DESC;

-- Q4: Manufacturer Inventory Summary
-- Show inventory status for all products owned by a manufacturer,
-- including nearly-out-of-stock items.

SELECT 
    p.product_id,
    p.name AS product_name,
    c.name AS category_name,
    p.standard_batch_size,
    COUNT(pb.lot_number) AS batches_produced,
    COALESCE(SUM(pb.quantity_produced), 0) AS total_units_produced,
    CASE 
        WHEN COALESCE(SUM(pb.quantity_produced), 0) < p.standard_batch_size 
        THEN 'NEARLY OUT OF STOCK'
        ELSE 'ADEQUATE'
    END AS stock_status
FROM PRODUCT p
JOIN CATEGORY c ON p.category_id = c.category_id
LEFT JOIN PRODUCT_BATCH pb ON p.product_id = pb.product_id
WHERE p.manufacturer_id = ? -- Parameter: manufacturer ID
GROUP BY p.product_id, p.name, c.name, p.standard_batch_size
ORDER BY stock_status DESC, p.name;

-- Q5: Compound Ingredient Material Breakdown
-- For compound ingredients, show their material composition 
-- and validate one-level nesting rule.

SELECT 
    parent.ingredient_id AS compound_ingredient_id,
    parent.name AS compound_name,
    parent_supplier.name AS compound_supplier,
    f.formulation_id,
    material.ingredient_id AS material_id,
    material.name AS material_name,
    material_supplier.name AS material_supplier,
    material.type AS material_type,
    fm.quantity_required AS material_quantity,
    -- Flag potential nesting violations (if material is compound and has its own materials)
    CASE 
        WHEN material.type = 'COMPOUND' AND EXISTS(
            SELECT 1 FROM FORMULATION f2 
            JOIN FORMULATION_MATERIAL fm2 ON f2.formulation_id = fm2.formulation_id
            WHERE f2.ingredient_id = material.ingredient_id
              AND (f2.effective_end_date IS NULL OR f2.effective_end_date >= CURRENT_DATE)
        ) THEN 'NESTING VIOLATION'
        ELSE 'OK'
    END AS nesting_status
FROM INGREDIENT parent
JOIN SUPPLIER parent_supplier ON parent.supplier_id = parent_supplier.supplier_id
JOIN FORMULATION f ON parent.ingredient_id = f.ingredient_id
JOIN FORMULATION_MATERIAL fm ON f.formulation_id = fm.formulation_id
JOIN INGREDIENT material ON fm.material_ingredient_id = material.ingredient_id
JOIN SUPPLIER material_supplier ON material.supplier_id = material_supplier.supplier_id
WHERE parent.type = 'COMPOUND'
  AND (f.effective_end_date IS NULL OR f.effective_end_date >= CURRENT_DATE)
  AND f.effective_start_date <= CURRENT_DATE
ORDER BY parent.name, parent_supplier.name, fm.quantity_required DESC;

-- Q6: Production Traceability Report
-- For a given product batch, trace all ingredient lots consumed
-- showing complete supply chain from supplier to finished product.

SELECT 
    pb.lot_number AS product_lot,
    p.name AS product_name,
    m.name AS manufacturer_name,
    pb.quantity_produced,
    pb.total_cost,
    pb.per_unit_cost,
    pb.production_date,
    ib.lot_number AS ingredient_lot,
    i.name AS ingredient_name,
    s.name AS supplier_name,
    bc.quantity_consumed,
    ib.expiration_date AS ingredient_expiry,
    (bc.quantity_consumed * ib.cost_per_unit) AS ingredient_cost_contribution
FROM PRODUCT_BATCH pb
JOIN PRODUCT p ON pb.product_id = p.product_id
JOIN MANUFACTURER m ON pb.manufacturer_id = m.manufacturer_id
JOIN BATCH_CONSUMPTION bc ON pb.lot_number = bc.product_batch_lot
JOIN INGREDIENT_BATCH ib ON bc.ingredient_batch_lot = ib.lot_number
JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
WHERE pb.lot_number = ? -- Parameter: specific product batch lot number
ORDER BY bc.quantity_consumed DESC;

-- Additional Validation Queries for Model Integrity

-- Q7: User Role Validation
-- Verify user-role mappings are consistent

SELECT 
    u.user_id,
    u.username,
    u.role,
    CASE u.role
        WHEN 'MANUFACTURER' THEN m.name
        WHEN 'SUPPLIER' THEN s.name
        WHEN 'VIEWER' THEN 'N/A'
    END AS entity_name,
    CASE 
        WHEN u.role = 'MANUFACTURER' AND m.manufacturer_id IS NULL THEN 'MISSING MANUFACTURER RECORD'
        WHEN u.role = 'SUPPLIER' AND s.supplier_id IS NULL THEN 'MISSING SUPPLIER RECORD'
        WHEN u.role = 'VIEWER' AND (m.manufacturer_id IS NOT NULL OR s.supplier_id IS NOT NULL) THEN 'VIEWER WITH ENTITY'
        ELSE 'OK'
    END AS validation_status
FROM USER u
LEFT JOIN MANUFACTURER m ON u.user_id = m.user_id
LEFT JOIN SUPPLIER s ON u.user_id = s.user_id
ORDER BY u.role, u.username;

-- Q8: Verify no overlapping formulation periods for same ingredient
SELECT 
    f1.ingredient_id,
    i.name AS ingredient_name,
    s.name AS supplier_name,
    f1.formulation_id AS formulation_1,
    f2.formulation_id AS formulation_2,
    f1.effective_start_date AS start_1,
    f1.effective_end_date AS end_1,
    f2.effective_start_date AS start_2,
    f2.effective_end_date AS end_2
FROM FORMULATION f1
JOIN FORMULATION f2 ON f1.ingredient_id = f2.ingredient_id
    AND f1.formulation_id != f2.formulation_id
JOIN INGREDIENT i ON f1.ingredient_id = i.ingredient_id
JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
WHERE (f1.effective_start_date <= COALESCE(f2.effective_end_date, '9999-12-31')
       AND COALESCE(f1.effective_end_date, '9999-12-31') >= f2.effective_start_date);

-- Q9: Verify lot number format compliance
SELECT 
    'INGREDIENT' AS batch_type,
    lot_number,
    ingredient_id,
    batch_id,
    CASE 
        WHEN lot_number REGEXP CONCAT('^', ingredient_id, '-[0-9]+-', batch_id, '$') THEN 'VALID'
        ELSE 'INVALID FORMAT'
    END AS format_status
FROM INGREDIENT_BATCH
WHERE lot_number NOT REGEXP CONCAT('^', ingredient_id, '-[0-9]+-', batch_id, '$')
UNION ALL
SELECT 
    'PRODUCT' AS batch_type,
    lot_number,
    product_id,
    batch_id,
    CASE 
        WHEN lot_number REGEXP CONCAT('^', product_id, '-[0-9]+-', batch_id, '$') THEN 'VALID'
        ELSE 'INVALID FORMAT'
    END AS format_status
FROM PRODUCT_BATCH
WHERE lot_number NOT REGEXP CONCAT('^', product_id, '-[0-9]+-', batch_id, '$');