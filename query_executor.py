"""
Query Executor Module
Executes the 5 required retrieval queries
"""


class QueryExecutor:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def display_menu(self):
        """Display query execution menu"""
        while True:
            print(f"\n{'='*50}")
            print("  EXECUTE QUERIES")
            print(f"{'='*50}")
            print("1. List all products and their categories")
            print("2. Last batch ingredients for Steak Dinner (100) by MFG001")
            print("3. Suppliers and total spent for MFG002")
            print("4. Manufacturers NOT supplied by Supplier B (21)")
            print("5. Unit cost for product lot 100-MFG001-B0901")
            print("6. Back")
            
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == '1':
                self.query_1_all_products()
            elif choice == '2':
                self.query_2_last_batch_ingredients()
            elif choice == '3':
                self.query_3_mfg002_suppliers()
            elif choice == '4':
                self.query_4_not_supplied_by_21()
            elif choice == '5':
                self.query_5_unit_cost()
            elif choice == '6':
                break
            else:
                print("\nInvalid choice.")
    
    def query_1_all_products(self):
        """Query 1: List all products and their categories"""
        print("\n=== QUERY 1: All Products and Categories ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    p.product_id,
                    p.name AS product_name,
                    c.name AS category_name,
                    m.name AS manufacturer_name
                FROM PRODUCT p
                JOIN CATEGORY c ON p.category_id = c.category_id
                JOIN MANUFACTURER m ON p.manufacturer_id = m.manufacturer_id
                ORDER BY c.name, p.name
            """)
            
            results = cursor.fetchall()
            
            if not results:
                print("\nNo products found.")
                return
            
            print(f"\n{'Product ID':<12} {'Product Name':<30} {'Category':<15} {'Manufacturer'}")
            print("-" * 85)
            
            for row in results:
                print(f"{row['product_id']:<12} {row['product_name']:<30} "
                      f"{row['category_name']:<15} {row['manufacturer_name']}")
            
            print(f"\nTotal products: {len(results)}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def query_2_last_batch_ingredients(self):
        """Query 2: List ingredients and lot numbers of last batch of Steak Dinner (100) by MFG001"""
        print("\n=== QUERY 2: Last Batch Ingredients for Steak Dinner (100) - MFG001 ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # First, get the last batch
            cursor.execute("""
                SELECT pb.lot_number, pb.production_date, pb.quantity_produced
                FROM PRODUCT_BATCH pb
                WHERE pb.product_id = 100
                  AND pb.manufacturer_id = 'MFG001'
                ORDER BY pb.production_date DESC
                LIMIT 1
            """)
            
            batch = cursor.fetchone()
            
            if not batch:
                print("\nNo batches found for Steak Dinner (100) by MFG001.")
                return
            
            print(f"\nLast Batch: {batch['lot_number']}")
            print(f"Production Date: {batch['production_date']}")
            print(f"Quantity Produced: {batch['quantity_produced']} units")
            
            # Now get ingredients for this batch
            cursor.execute("""
                SELECT 
                    pb.lot_number AS product_lot,
                    pb.production_date,
                    i.ingredient_id,
                    i.name AS ingredient_name,
                    ib.lot_number AS ingredient_lot,
                    bc.quantity_consumed
                FROM PRODUCT_BATCH pb
                JOIN BATCH_CONSUMPTION bc ON pb.lot_number = bc.product_batch_lot
                JOIN INGREDIENT_BATCH ib ON bc.ingredient_batch_lot = ib.lot_number
                JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
                WHERE pb.lot_number = %s
                ORDER BY bc.quantity_consumed DESC
            """, (batch['lot_number'],))
            
            ingredients = cursor.fetchall()
            
            if not ingredients:
                print("\nNo ingredients found for this batch.")
                return
            
            print(f"\n{'Ingredient ID':<15} {'Ingredient Name':<30} {'Ingredient Lot':<20} {'Quantity (oz)'}")
            print("-" * 90)
            
            for row in ingredients:
                print(f"{row['ingredient_id']:<15} {row['ingredient_name']:<30} "
                      f"{row['ingredient_lot']:<20} {row['quantity_consumed']:>13.2f}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def query_3_mfg002_suppliers(self):
        """Query 3: For MFG002, list all suppliers and total spent per supplier"""
        print("\n=== QUERY 3: Suppliers and Total Spent for MFG002 ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    s.supplier_id,
                    s.name AS supplier_name,
                    SUM(bc.quantity_consumed * ib.cost_per_unit) AS total_spent
                FROM PRODUCT_BATCH pb
                JOIN BATCH_CONSUMPTION bc ON pb.lot_number = bc.product_batch_lot
                JOIN INGREDIENT_BATCH ib ON bc.ingredient_batch_lot = ib.lot_number
                JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
                JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
                WHERE pb.manufacturer_id = 'MFG002'
                GROUP BY s.supplier_id, s.name
                ORDER BY total_spent DESC
            """)
            
            results = cursor.fetchall()
            
            if not results:
                print("\nNo supplier purchases found for MFG002.")
                return
            
            print(f"\n{'Supplier ID':<15} {'Supplier Name':<30} {'Total Spent'}")
            print("-" * 60)
            
            total = 0
            for row in results:
                print(f"{row['supplier_id']:<15} {row['supplier_name']:<30} ${row['total_spent']:>10.2f}")
                total += row['total_spent']
            
            print("-" * 60)
            print(f"{'TOTAL':<45} ${total:>10.2f}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def query_4_not_supplied_by_21(self):
        """Query 4: Which manufacturers has Supplier B (21) NOT supplied to?"""
        print("\n=== QUERY 4: Manufacturers NOT Supplied by Supplier B (21) ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    m.manufacturer_id,
                    m.name AS manufacturer_name
                FROM MANUFACTURER m
                WHERE m.manufacturer_id NOT IN (
                    SELECT DISTINCT pb.manufacturer_id
                    FROM PRODUCT_BATCH pb
                    JOIN BATCH_CONSUMPTION bc ON pb.lot_number = bc.product_batch_lot
                    JOIN INGREDIENT_BATCH ib ON bc.ingredient_batch_lot = ib.lot_number
                    JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
                    WHERE i.supplier_id = 21
                )
                ORDER BY m.name
            """)
            
            results = cursor.fetchall()
            
            if not results:
                print("\nAll manufacturers have been supplied by Supplier B (21).")
                return
            
            print(f"\n{'Manufacturer ID':<20} {'Manufacturer Name'}")
            print("-" * 50)
            
            for row in results:
                print(f"{row['manufacturer_id']:<20} {row['manufacturer_name']}")
            
            print(f"\nTotal manufacturers NOT supplied: {len(results)}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def query_5_unit_cost(self):
        """Query 5: Find unit cost for product lot 100-MFG001-B0901"""
        print("\n=== QUERY 5: Unit Cost for Product Lot 100-MFG001-B0901 ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    pb.lot_number,
                    p.name AS product_name,
                    pb.per_unit_cost,
                    pb.total_cost,
                    pb.quantity_produced,
                    pb.production_date
                FROM PRODUCT_BATCH pb
                JOIN PRODUCT p ON pb.product_id = p.product_id
                WHERE pb.lot_number = '100-MFG001-B0901'
            """)
            
            result = cursor.fetchone()
            
            if not result:
                print("\nProduct batch lot 100-MFG001-B0901 not found.")
                return
            
            print(f"\nProduct: {result['product_name']}")
            print(f"Lot Number: {result['lot_number']}")
            print(f"Production Date: {result['production_date']}")
            print(f"Quantity Produced: {result['quantity_produced']} units")
            print(f"Total Batch Cost: ${result['total_cost']:.2f}")
            print(f"Per Unit Cost: ${result['per_unit_cost']:.4f}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()