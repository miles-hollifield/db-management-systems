"""
Viewer Menu Module
Handles all viewer (read-only) operations
"""


class ViewerMenu:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def display_menu(self):
        """Display viewer menu and handle choices"""
        while True:
            print(f"\n{'='*50}")
            print(f"  VIEWER MENU")
            print(f"{'='*50}")
            print("1. Browse Products")
            print("2. Generate Ingredient List")
            print("3. Execute Queries")
            print("4. Logout")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                self.browse_products()
            elif choice == '2':
                self.generate_ingredient_list()
            elif choice == '3':
                self.execute_queries()
            elif choice == '4':
                print("\nLogging out...")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def browse_products(self):
        """Browse all products organized by manufacturer and category"""
        print("\n=== BROWSE PRODUCTS ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    p.product_id,
                    p.name AS product_name,
                    c.name AS category_name,
                    m.name AS manufacturer_name,
                    p.standard_batch_size
                FROM PRODUCT p
                JOIN CATEGORY c ON p.category_id = c.category_id
                JOIN MANUFACTURER m ON p.manufacturer_id = m.manufacturer_id
                ORDER BY m.name, c.name, p.name
            """)
            
            products = cursor.fetchall()
            
            if not products:
                print("\nNo products available.")
                return
            
            print(f"\n{'ID':<8} {'Product':<30} {'Category':<15} {'Manufacturer':<20} {'Batch Size'}")
            print("-" * 100)
            
            current_manufacturer = None
            for p in products:
                # Print manufacturer header when it changes
                if current_manufacturer != p['manufacturer_name']:
                    current_manufacturer = p['manufacturer_name']
                    print(f"\n--- {current_manufacturer} ---")
                
                print(f"{p['product_id']:<8} {p['product_name']:<30} {p['category_name']:<15} "
                      f"{p['manufacturer_name']:<20} {p['standard_batch_size']}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def generate_ingredient_list(self):
        """
        Generate ingredient list for a product batch
        Flow: Product → Product Batch → Ingredient List
        """
        print("\n=== GENERATE INGREDIENT LIST ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Step 1: Select a product
            cursor.execute("""
                SELECT DISTINCT p.product_id, p.name, m.name AS manufacturer_name
                FROM PRODUCT p
                JOIN MANUFACTURER m ON p.manufacturer_id = m.manufacturer_id
                JOIN PRODUCT_BATCH pb ON p.product_id = pb.product_id
                ORDER BY p.name
            """)
            
            products = cursor.fetchall()
            
            if not products:
                print("\nNo products with batches found.")
                return
            
            print("\n--- Available Products ---")
            for p in products:
                print(f"{p['product_id']}. {p['name']} ({p['manufacturer_name']})")
            
            product_id = int(input("\nSelect Product ID: ").strip())
            
            # Step 2: Select a product batch
            cursor.execute("""
                SELECT pb.lot_number, pb.production_date, pb.quantity_produced
                FROM PRODUCT_BATCH pb
                WHERE pb.product_id = %s
                ORDER BY pb.production_date DESC
            """, (product_id,))
            
            batches = cursor.fetchall()
            
            if not batches:
                print("\nNo batches found for this product.")
                return
            
            print("\n--- Available Product Batches ---")
            for b in batches:
                print(f"{b['lot_number']} - Produced: {b['production_date']}, Qty: {b['quantity_produced']}")
            
            product_batch_lot = input("\nSelect Product Batch Lot Number: ").strip()
            
            # Step 3: Display ingredients consumed in that batch
            cursor.execute("""
                SELECT 
                    i.ingredient_id,
                    i.name AS ingredient_name,
                    s.name AS supplier_name,
                    i.type,
                    bc.quantity_consumed
                FROM BATCH_CONSUMPTION bc
                JOIN INGREDIENT_BATCH ib ON bc.ingredient_batch_lot = ib.lot_number
                JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
                JOIN SUPPLIER s ON i.supplier_id = s.supplier_id
                WHERE bc.product_batch_lot = %s
                ORDER BY bc.quantity_consumed DESC, i.name
            """, (product_batch_lot,))
            
            ingredients = cursor.fetchall()
            
            if not ingredients:
                print("\nNo ingredients found for this batch.")
                return
            
            print(f"\n=== Ingredient List for Batch {product_batch_lot} ===")
            print(f"\n{'Ingredient':<40} {'Type':<12} {'Supplier':<20} {'Quantity (oz)'}")
            print("-" * 90)
            
            for ing in ingredients:
                print(f"{ing['ingredient_name']:<40} {ing['type']:<12} "
                      f"{ing['supplier_name']:<20} {ing['quantity_consumed']:>12.2f}")
            
            # If any compound ingredients, show their materials
            compound_ingredients = [ing for ing in ingredients if ing['type'] == 'COMPOUND']
            
            if compound_ingredients:
                print("\n--- Compound Ingredient Materials ---")
                
                for comp in compound_ingredients:
                    print(f"\n{comp['ingredient_name']} contains:")
                    
                    # Get materials for this compound ingredient
                    cursor.execute("""
                        SELECT 
                            i.name AS material_name,
                            fm.quantity_required
                        FROM FORMULATION f
                        JOIN FORMULATION_MATERIAL fm ON f.formulation_id = fm.formulation_id
                        JOIN INGREDIENT i ON fm.material_ingredient_id = i.ingredient_id
                        WHERE f.ingredient_id = %s
                          AND (f.effective_end_date IS NULL OR f.effective_end_date >= CURRENT_DATE)
                          AND f.effective_start_date <= CURRENT_DATE
                        ORDER BY fm.quantity_required DESC
                    """, (comp['ingredient_id'],))
                    
                    materials = cursor.fetchall()
                    
                    for mat in materials:
                        print(f"  - {mat['material_name']}: {mat['quantity_required']} oz")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def execute_queries(self):
        """Execute required retrieval queries"""
        from query_executor import QueryExecutor
        executor = QueryExecutor(self.db)
        executor.display_menu()