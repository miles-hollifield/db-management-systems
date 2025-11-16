-- CSC440 Project: Inventory Management for Prepared/Frozen Meals Manufacturer
-- SQL DDL Schema - UPDATED with clarifications

-- Team Members:
-- Miles Hollifield (mfhollif)
-- Claire Jeffries (cmjeffri)

-- ============================================================
-- SECTION 1: TABLE CREATION
-- ============================================================

-- User Management System

CREATE TABLE USER (
    user_id INT AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('MANUFACTURER', 'SUPPLIER', 'VIEWER') NOT NULL,
    created_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (user_id)
);

CREATE TABLE MANUFACTURER (
    manufacturer_id VARCHAR(20),
    user_id INT NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY (manufacturer_id),
    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE
);

CREATE TABLE SUPPLIER (
    supplier_id INT AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY (supplier_id),
    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE
);

-- Core Domain Entities

CREATE TABLE CATEGORY (
    category_id INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    PRIMARY KEY (category_id)
);

CREATE TABLE PRODUCT (
    product_id INT AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    manufacturer_id VARCHAR(20) NOT NULL,
    standard_batch_size INT NOT NULL,
    PRIMARY KEY (product_id),
    FOREIGN KEY (category_id) REFERENCES CATEGORY(category_id) ON DELETE RESTRICT,
    FOREIGN KEY (manufacturer_id) REFERENCES MANUFACTURER(manufacturer_id) ON DELETE RESTRICT,
    CHECK (standard_batch_size > 0)
);

CREATE TABLE INGREDIENT (
    ingredient_id INT AUTO_INCREMENT,
    supplier_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    type ENUM('ATOMIC', 'COMPOUND') NOT NULL,
    PRIMARY KEY (ingredient_id),
    FOREIGN KEY (supplier_id) REFERENCES SUPPLIER(supplier_id) ON DELETE CASCADE
);

-- Recipe Management (Versioned)

CREATE TABLE RECIPE_PLAN (
    plan_id INT AUTO_INCREMENT,
    product_id INT NOT NULL,
    version_number INT NOT NULL,
    created_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (plan_id),
    FOREIGN KEY (product_id) REFERENCES PRODUCT(product_id) ON DELETE CASCADE,
    UNIQUE KEY unique_product_version (product_id, version_number),
    CHECK (version_number > 0)
);

CREATE TABLE RECIPE_INGREDIENT (
    plan_id INT,
    ingredient_id INT,
    quantity_required DECIMAL(10,3) NOT NULL,
    PRIMARY KEY (plan_id, ingredient_id),
    FOREIGN KEY (plan_id) REFERENCES RECIPE_PLAN(plan_id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES INGREDIENT(ingredient_id) ON DELETE RESTRICT,
    CHECK (quantity_required > 0)
);

-- Supplier Formulations (Pricing & Versioning for Ingredients)

CREATE TABLE FORMULATION (
    formulation_id INT AUTO_INCREMENT,
    ingredient_id INT NOT NULL,
    pack_size DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    effective_start_date DATE NOT NULL,
    effective_end_date DATE NULL,
    PRIMARY KEY (formulation_id),
    FOREIGN KEY (ingredient_id) REFERENCES INGREDIENT(ingredient_id) ON DELETE CASCADE,
    UNIQUE KEY unique_ingredient_start (ingredient_id, effective_start_date),
    CHECK (pack_size > 0),
    CHECK (unit_price > 0),
    CHECK (effective_end_date IS NULL OR effective_end_date > effective_start_date)
);

CREATE TABLE FORMULATION_MATERIAL (
    formulation_id INT,
    material_ingredient_id INT,
    quantity_required DECIMAL(10,3) NOT NULL,
    PRIMARY KEY (formulation_id, material_ingredient_id),
    FOREIGN KEY (formulation_id) REFERENCES FORMULATION(formulation_id) ON DELETE CASCADE,
    FOREIGN KEY (material_ingredient_id) REFERENCES INGREDIENT(ingredient_id) ON DELETE RESTRICT,
    CHECK (quantity_required > 0)
);

-- Batch/Lot Tracking

CREATE TABLE INGREDIENT_BATCH (
    lot_number VARCHAR(50),
    ingredient_id INT NOT NULL,
    supplier_id INT NOT NULL,
    manufacturer_id VARCHAR(20) NULL,
    batch_id VARCHAR(20) NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    cost_per_unit DECIMAL(10,2) NOT NULL,
    expiration_date DATE NOT NULL,
    received_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    on_hand_oz DECIMAL(10,3) DEFAULT 0,
    PRIMARY KEY (lot_number),
    FOREIGN KEY (ingredient_id) REFERENCES INGREDIENT(ingredient_id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES SUPPLIER(supplier_id) ON DELETE RESTRICT,
    FOREIGN KEY (manufacturer_id) REFERENCES MANUFACTURER(manufacturer_id) ON DELETE RESTRICT,
    CHECK (quantity >= 0),
    CHECK (cost_per_unit > 0)
);

CREATE TABLE PRODUCT_BATCH (
    lot_number VARCHAR(50),
    product_id INT NOT NULL,
    manufacturer_id VARCHAR(20) NOT NULL,
    plan_id INT NOT NULL,
    batch_id VARCHAR(20) NOT NULL,
    quantity_produced INT NOT NULL,
    total_cost DECIMAL(12,2) NOT NULL,
    per_unit_cost DECIMAL(10,4) NOT NULL,
    production_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (lot_number),
    FOREIGN KEY (product_id) REFERENCES PRODUCT(product_id) ON DELETE RESTRICT,
    FOREIGN KEY (manufacturer_id) REFERENCES MANUFACTURER(manufacturer_id) ON DELETE RESTRICT,
    FOREIGN KEY (plan_id) REFERENCES RECIPE_PLAN(plan_id) ON DELETE RESTRICT,
    CHECK (quantity_produced > 0),
    CHECK (total_cost >= 0),
    CHECK (per_unit_cost >= 0)
);

CREATE TABLE BATCH_CONSUMPTION (
    product_batch_lot VARCHAR(50),
    ingredient_batch_lot VARCHAR(50),
    quantity_consumed DECIMAL(10,3) NOT NULL,
    PRIMARY KEY (product_batch_lot, ingredient_batch_lot),
    FOREIGN KEY (product_batch_lot) REFERENCES PRODUCT_BATCH(lot_number) ON DELETE RESTRICT,
    FOREIGN KEY (ingredient_batch_lot) REFERENCES INGREDIENT_BATCH(lot_number) ON DELETE RESTRICT,
    CHECK (quantity_consumed > 0)
);

-- ============================================================
-- SECTION 2: INDEXES
-- ============================================================

CREATE INDEX idx_user_role ON USER(role);
CREATE INDEX idx_manufacturer_user ON MANUFACTURER(user_id);
CREATE INDEX idx_supplier_user ON SUPPLIER(user_id);
CREATE INDEX idx_ingredient_supplier ON INGREDIENT(supplier_id);
CREATE INDEX idx_product_manufacturer ON PRODUCT(manufacturer_id);
CREATE INDEX idx_product_category ON PRODUCT(category_id);
CREATE INDEX idx_recipe_plan_product ON RECIPE_PLAN(product_id);
CREATE INDEX idx_recipe_plan_active ON RECIPE_PLAN(product_id, is_active);
CREATE INDEX idx_formulation_ingredient ON FORMULATION(ingredient_id);
CREATE INDEX idx_formulation_dates ON FORMULATION(effective_start_date, effective_end_date);
CREATE INDEX idx_ingredient_batch_ingredient ON INGREDIENT_BATCH(ingredient_id);
CREATE INDEX idx_ingredient_batch_supplier ON INGREDIENT_BATCH(supplier_id);
CREATE INDEX idx_ingredient_batch_manufacturer ON INGREDIENT_BATCH(manufacturer_id);
CREATE INDEX idx_ingredient_batch_expiration ON INGREDIENT_BATCH(expiration_date);
CREATE INDEX idx_product_batch_manufacturer ON PRODUCT_BATCH(manufacturer_id);
CREATE INDEX idx_product_batch_product ON PRODUCT_BATCH(product_id);

-- ============================================================
-- SECTION 3: INITIAL DATA
-- ============================================================

INSERT INTO CATEGORY (name) VALUES ('Dinners'), ('Sides'), ('Desserts');

-- ============================================================
-- SECTION 4: TRIGGERS
-- ============================================================

DELIMITER $$

-- Trigger 1: Compute ingredient lot number
-- User provides ingredient_id, supplier_id, batch_id
-- Trigger generates lot_number and checks for duplicates
CREATE TRIGGER trg_compute_ingredient_lot_number
BEFORE INSERT ON INGREDIENT_BATCH
FOR EACH ROW
BEGIN
    DECLARE new_lot VARCHAR(50);

    -- Construct lot number: ingredientId-supplierId-batchId
    SET new_lot = CONCAT(NEW.ingredient_id, '-', NEW.supplier_id, '-', NEW.batch_id);
    
    -- Check for duplicate
    IF EXISTS (SELECT 1 FROM INGREDIENT_BATCH WHERE lot_number = new_lot) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Duplicate lot number detected.';
    END IF;
    
    -- Set the lot number
    SET NEW.lot_number = new_lot;
END$$

-- Trigger 2: Initialize on-hand quantity on insert
CREATE TRIGGER trg_initialize_on_hand
BEFORE INSERT ON INGREDIENT_BATCH
FOR EACH ROW
BEGIN
    SET NEW.on_hand_oz = NEW.quantity;
END$$

-- Trigger 3: Prevent expired consumption
CREATE TRIGGER trg_prevent_expired_consumption
BEFORE INSERT ON BATCH_CONSUMPTION
FOR EACH ROW
BEGIN
    DECLARE exp_date DATE;

    SELECT expiration_date INTO exp_date
    FROM INGREDIENT_BATCH
    WHERE lot_number = NEW.ingredient_batch_lot;

    IF exp_date < CURRENT_DATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot consume expired ingredient lot.';
    END IF;
END$$

-- Trigger 4: Decrement on-hand on consumption
CREATE TRIGGER trg_decrement_on_hand
BEFORE INSERT ON BATCH_CONSUMPTION
FOR EACH ROW
BEGIN
    DECLARE current_qty DECIMAL(10,3);

    SELECT on_hand_oz INTO current_qty
    FROM INGREDIENT_BATCH
    WHERE lot_number = NEW.ingredient_batch_lot;

    IF current_qty < NEW.quantity_consumed THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient quantity in ingredient lot.';
    ELSE
        UPDATE INGREDIENT_BATCH
        SET on_hand_oz = on_hand_oz - NEW.quantity_consumed
        WHERE lot_number = NEW.ingredient_batch_lot;
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- SECTION 5: STORED PROCEDURES
-- ============================================================

-- Stored Procedure - RecordProductionBatch
-- Creates a new product batch, consumes ingredient lots,
-- updates inventory, and calculates total and per-unit cost
DELIMITER $$

CREATE PROCEDURE RecordProductionBatch (
    IN in_product_id INT,
    IN in_plan_id INT,
    IN in_manufacturer_id VARCHAR(20),
    IN in_batch_id VARCHAR(20),
    IN in_produced_units INT,
    IN in_ingredient_list JSON
)
BEGIN
    DECLARE total_cost DECIMAL(12,2) DEFAULT 0.0;
    DECLARE per_unit_cost DECIMAL(12,4);
    DECLARE lot_num VARCHAR(50);
    DECLARE ingr_lot VARCHAR(50);
    DECLARE ingr_qty DECIMAL(10,3);
    DECLARE ingr_cost DECIMAL(10,2);
    DECLARE std_batch_size INT;
    DECLARE i INT DEFAULT 0;
    DECLARE n INT;

    SELECT standard_batch_size INTO std_batch_size
    FROM PRODUCT
    WHERE product_id = in_product_id;

    IF in_produced_units % std_batch_size != 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Produced units must be a multiple of standard batch size.';
    END IF;

    SET lot_num = CONCAT(in_product_id, '-', in_manufacturer_id, '-', in_batch_id);

    IF EXISTS (SELECT 1 FROM PRODUCT_BATCH WHERE lot_number = lot_num) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Product batch lot number already exists.';
    END IF;

    INSERT INTO PRODUCT_BATCH (
        lot_number, product_id, manufacturer_id, plan_id, batch_id,
        quantity_produced, total_cost, per_unit_cost, production_date
    ) VALUES (
        lot_num, in_product_id, in_manufacturer_id, in_plan_id, in_batch_id,
        in_produced_units, 0, 0, CURRENT_DATE()
    );

    SET n = JSON_LENGTH(in_ingredient_list);

    WHILE i < n DO
        SET ingr_lot = JSON_UNQUOTE(JSON_EXTRACT(in_ingredient_list, CONCAT('$[', i, '].lot')));
        SET ingr_qty = JSON_UNQUOTE(JSON_EXTRACT(in_ingredient_list, CONCAT('$[', i, '].qty')));

        -- get ingredient unit cost
        SELECT cost_per_unit INTO ingr_cost
        FROM INGREDIENT_BATCH
        WHERE lot_number = ingr_lot;

        -- calculate cost contribution
        SET total_cost = total_cost + (ingr_cost * ingr_qty);

        -- insert consumption record
        INSERT INTO BATCH_CONSUMPTION (product_batch_lot, ingredient_batch_lot, quantity_consumed)
        VALUES (lot_num, ingr_lot, ingr_qty);

        SET i = i + 1;
    END WHILE;

    SET per_unit_cost = total_cost / in_produced_units;

    UPDATE PRODUCT_BATCH
    SET total_cost = total_cost, per_unit_cost = per_unit_cost
    WHERE lot_number = lot_num;

    SELECT 
        lot_num AS product_lot,
        in_product_id AS product_id,
        total_cost AS batch_total_cost,
        per_unit_cost AS unit_cost,
        in_produced_units AS produced_units;
END$$

DELIMITER ;

-- ============================================================
-- SECTION 6: VIEWS
-- ============================================================

CREATE OR REPLACE VIEW vw_active_formulations AS
SELECT 
    f.formulation_id,
    s.supplier_id,
    s.name AS supplier_name,
    i.ingredient_id,
    i.name AS ingredient_name,
    i.type AS ingredient_type,
    f.pack_size,
    f.unit_price,
    f.effective_start_date,
    f.effective_end_date
FROM FORMULATION f
JOIN INGREDIENT i ON f.ingredient_id = i.ingredient_id
JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
WHERE (f.effective_end_date IS NULL OR f.effective_end_date >= CURRENT_DATE)
  AND f.effective_start_date <= CURRENT_DATE;

CREATE OR REPLACE VIEW vw_flattened_product_bom AS
SELECT 
    p.product_id,
    p.name AS product_name,
    m.name AS manufacturer_name,
    rp.plan_id,
    rp.version_number,
    i.ingredient_id,
    i.name AS ingredient_name,
    s.name AS supplier_name,
    i.type AS ingredient_type,
    ri.quantity_required
FROM PRODUCT p
JOIN MANUFACTURER m ON p.manufacturer_id = m.manufacturer_id
JOIN RECIPE_PLAN rp ON p.product_id = rp.product_id
JOIN RECIPE_INGREDIENT ri ON rp.plan_id = ri.plan_id
JOIN INGREDIENT i ON ri.ingredient_id = i.ingredient_id
JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
WHERE rp.is_active = TRUE
ORDER BY p.product_id, ri.quantity_required DESC, i.name;

-- ============================================================
-- SECTION 7: REQUIRED RETRIEVAL QUERIES
-- ============================================================

-- Query 1: List all products and their categories
-- SELECT 
--     p.product_id,
--     p.name AS product_name,
--     c.name AS category_name,
--     m.name AS manufacturer_name
-- FROM PRODUCT p
-- JOIN CATEGORY c ON p.category_id = c.category_id
-- JOIN MANUFACTURER m ON p.manufacturer_id = m.manufacturer_id
-- ORDER BY c.name, p.name;

-- Query 2: List ingredients and lot numbers of last batch of Steak Dinner (100) by MFG001
-- SELECT 
--     pb.lot_number AS product_lot,
--     pb.production_date,
--     i.ingredient_id,
--     i.name AS ingredient_name,
--     ib.lot_number AS ingredient_lot,
--     bc.quantity_consumed
-- FROM PRODUCT_BATCH pb
-- JOIN BATCH_CONSUMPTION bc ON pb.lot_number = bc.product_batch_lot
-- JOIN INGREDIENT_BATCH ib ON bc.ingredient_batch_lot = ib.lot_number
-- JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
-- WHERE pb.product_id = 100
--   AND pb.manufacturer_id = 'MFG001'
-- ORDER BY pb.production_date DESC
-- LIMIT 1;

-- Query 3: For MFG002, list suppliers and total spent per supplier
-- SELECT 
--     s.supplier_id,
--     s.name AS supplier_name,
--     SUM(bc.quantity_consumed * ib.cost_per_unit) AS total_spent
-- FROM PRODUCT_BATCH pb
-- JOIN BATCH_CONSUMPTION bc ON pb.lot_number = bc.product_batch_lot
-- JOIN INGREDIENT_BATCH ib ON bc.ingredient_batch_lot = ib.lot_number
-- JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
-- JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
-- WHERE pb.manufacturer_id = 'MFG002'
-- GROUP BY s.supplier_id, s.name
-- ORDER BY total_spent DESC;

-- Query 4: Which manufacturers has Supplier B (21) NOT supplied to?
-- SELECT 
--     m.manufacturer_id,
--     m.name AS manufacturer_name
-- FROM MANUFACTURER m
-- WHERE m.manufacturer_id NOT IN (
--     SELECT DISTINCT pb.manufacturer_id
--     FROM PRODUCT_BATCH pb
--     JOIN BATCH_CONSUMPTION bc ON pb.lot_number = bc.product_batch_lot
--     JOIN INGREDIENT_BATCH ib ON bc.ingredient_batch_lot = ib.lot_number
--     JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
--     WHERE i.supplier_id = 21
-- )
-- ORDER BY m.name;

-- Query 5: Unit cost for product lot 100-MFG001-B0901
-- SELECT 
--     pb.lot_number,
--     p.name AS product_name,
--     pb.per_unit_cost,
--     pb.total_cost,
--     pb.quantity_produced
-- FROM PRODUCT_BATCH pb
-- JOIN PRODUCT p ON pb.product_id = p.product_id
-- WHERE pb.lot_number = '100-MFG001-B0901';