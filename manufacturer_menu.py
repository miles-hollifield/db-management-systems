"""
Manufacturer Menu Module
Handles all manufacturer-specific operations
"""

from datetime import datetime, timedelta
import json


class ManufacturerMenu:
    def __init__(self, db_connection, user):
        self.db = db_connection
        self.user = user
        self.manufacturer_id = user['manufacturer_id']
        
    def display_menu(self):
        """Display manufacturer menu and handle choices"""
        while True:
            print(f"\n{'='*50}")
            print(f"  MANUFACTURER MENU - {self.user['name']}")
            print(f"{'='*50}")
            print("1. Create/Update Product")
            print("2. Create/Update Recipe Plan")
            print("3. Receive Ingredient Batch")
            print("4. Create Product Batch")
            print("5. Reports")
            print("6. Execute Queries")
            print("7. Logout")
            
            choice = input("\nEnter choice (1-7): ").strip()
            
            if choice == '1':
                self.create_product()
            elif choice == '2':
                self.create_recipe_plan()
            elif choice == '3':
                self.receive_ingredient_batch()
            elif choice == '4':
                self.create_product_batch()
            elif choice == '5':
                self.reports_menu()
            elif choice == '6':
                self.execute_queries()
            elif choice == '7':
                print("\nLogging out...")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def create_product(self):
        """Create a new product"""
        print("\n=== CREATE PRODUCT ===")
        
        # Show categories
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT category_id, name FROM CATEGORY")
            categories = cursor.fetchall()
            
            print("\nAvailable Categories:")
            for cat in categories:
                print(f"{cat['category_id']}. {cat['name']}")
            
            # Get product details
            name = input("\nProduct name: ").strip()
            category_id = int(input("Category ID: ").strip())
            standard_batch_size = int(input("Standard batch size: ").strip())
            
            # Insert product
            cursor.execute("""
                INSERT INTO PRODUCT (name, category_id, manufacturer_id, standard_batch_size)
                VALUES (%s, %s, %s, %s)
            """, (name, category_id, self.manufacturer_id, standard_batch_size))
            
            connection.commit()
            product_id = cursor.lastrowid
            
            print(f"\n✓ Product created successfully! Product ID: {product_id}")
            
        except Exception as e:
            connection.rollback()
            print(f"\n✗ Error creating product: {e}")
        finally:
            cursor.close()
    
    def create_recipe_plan(self):
        """Create a new recipe plan for a product"""
        print("\n=== CREATE RECIPE PLAN ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Show manufacturer's products
            cursor.execute("""
                SELECT product_id, name
                FROM PRODUCT
                WHERE manufacturer_id = %s
            """, (self.manufacturer_id,))
            
            products = cursor.fetchall()
            
            if not products:
                print("\nNo products found. Create a product first.")
                return
            
            print("\nYour Products:")
            for p in products:
                print(f"{p['product_id']}. {p['name']}")
            
            product_id = int(input("\nSelect Product ID: ").strip())
            
            # Get next version number
            cursor.execute("""
                SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
                FROM RECIPE_PLAN
                WHERE product_id = %s
            """, (product_id,))
            
            next_version = cursor.fetchone()['next_version']
            
            # Create recipe plan
            cursor.execute("""
                INSERT INTO RECIPE_PLAN (product_id, version_number, created_date, is_active)
                VALUES (%s, %s, CURRENT_DATE, FALSE)
            """, (product_id, next_version))
            
            plan_id = cursor.lastrowid
            
            print(f"\nRecipe Plan ID: {plan_id}, Version: {next_version}")
            
            # Add ingredients
            print("\n--- Add Ingredients to Recipe ---")
            
            while True:
                # Show available ingredients
                cursor.execute("""
                    SELECT ingredient_id, name, type
                    FROM INGREDIENT
                    ORDER BY name
                """)
                
                ingredients = cursor.fetchall()
                
                print("\nAvailable Ingredients (showing first 20):")
                for i, ing in enumerate(ingredients[:20]):
                    print(f"{ing['ingredient_id']}. {ing['name']} ({ing['type']})")
                
                ingredient_id = input("\nIngredient ID (or 'done' to finish): ").strip()
                
                if ingredient_id.lower() == 'done':
                    break
                
                quantity = float(input("Quantity required (ounces per unit): ").strip())
                
                cursor.execute("""
                    INSERT INTO RECIPE_INGREDIENT (plan_id, ingredient_id, quantity_required)
                    VALUES (%s, %s, %s)
                """, (plan_id, int(ingredient_id), quantity))
                
                print("✓ Ingredient added")
            
            # Ask if this should be the active recipe
            make_active = input("\nSet this as the active recipe? (y/n): ").strip().lower()
            
            if make_active == 'y':
                # Deactivate all other recipes for this product
                cursor.execute("""
                    UPDATE RECIPE_PLAN
                    SET is_active = FALSE
                    WHERE product_id = %s
                """, (product_id,))
                
                # Activate this recipe
                cursor.execute("""
                    UPDATE RECIPE_PLAN
                    SET is_active = TRUE
                    WHERE plan_id = %s
                """, (plan_id,))
            
            connection.commit()
            print(f"\n✓ Recipe plan created successfully!")
            
        except Exception as e:
            connection.rollback()
            print(f"\n✗ Error creating recipe plan: {e}")
        finally:
            cursor.close()
    
    def receive_ingredient_batch(self):
        """Receive an ingredient batch (with 90-day rule enforcement)"""
        print("\n=== RECEIVE INGREDIENT BATCH ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Get input
            ingredient_id = int(input("Ingredient ID: ").strip())
            supplier_id = int(input("Supplier ID: ").strip())
            batch_id = input("Batch ID: ").strip()
            quantity = float(input("Quantity (ounces): ").strip())
            cost_per_unit = float(input("Cost per unit: ").strip())
            expiration_date = input("Expiration date (YYYY-MM-DD): ").strip()
            
            # Validate 90-day rule (APPLICATION LOGIC)
            exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
            today = datetime.now()
            min_expiration = today + timedelta(days=90)
            
            if exp_date < min_expiration:
                print(f"\n✗ Error: Expiration date must be at least 90 days from today.")
                print(f"   Minimum allowed: {min_expiration.strftime('%Y-%m-%d')}")
                return
            
            # Insert ingredient batch
            cursor.execute("""
                INSERT INTO INGREDIENT_BATCH 
                (ingredient_id, supplier_id, manufacturer_id, batch_id, quantity, 
                 cost_per_unit, expiration_date, received_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
            """, (ingredient_id, supplier_id, self.manufacturer_id, batch_id, 
                  quantity, cost_per_unit, expiration_date))
            
            connection.commit()
            
            # Get the generated lot number
            cursor.execute("""
                SELECT lot_number 
                FROM INGREDIENT_BATCH 
                WHERE ingredient_id = %s AND supplier_id = %s AND batch_id = %s
            """, (ingredient_id, supplier_id, batch_id))
            
            result = cursor.fetchone()
            lot_number = result['lot_number'] if result else 'Unknown'
            
            print(f"\n✓ Ingredient batch received successfully!")
            print(f"   Lot Number: {lot_number}")
            
        except Exception as e:
            connection.rollback()
            print(f"\n✗ Error receiving ingredient batch: {e}")
        finally:
            cursor.close()
    
    def create_product_batch(self):
        """Create a product batch using stored procedure"""
        print("\n=== CREATE PRODUCT BATCH ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Show manufacturer's products with active recipes
            cursor.execute("""
                SELECT p.product_id, p.name, p.standard_batch_size, rp.plan_id, rp.version_number
                FROM PRODUCT p
                JOIN RECIPE_PLAN rp ON p.product_id = rp.product_id
                WHERE p.manufacturer_id = %s AND rp.is_active = TRUE
            """, (self.manufacturer_id,))
            
            products = cursor.fetchall()
            
            if not products:
                print("\nNo products with active recipes found.")
                return
            
            print("\nProducts with Active Recipes:")
            for p in products:
                print(f"{p['product_id']}. {p['name']} (Batch Size: {p['standard_batch_size']})")
            
            product_id = int(input("\nSelect Product ID: ").strip())
            
            # Get product details
            product = next((p for p in products if p['product_id'] == product_id), None)
            if not product:
                print("\nInvalid product ID.")
                return
            
            plan_id = product['plan_id']
            batch_id = input("Batch ID: ").strip()
            produced_units = int(input(f"Units to produce (multiple of {product['standard_batch_size']}): ").strip())
            
            # Validate multiple
            if produced_units % product['standard_batch_size'] != 0:
                print(f"\n✗ Units must be a multiple of {product['standard_batch_size']}")
                return
            
            # Show required ingredients
            cursor.execute("""
                SELECT ri.ingredient_id, i.name, ri.quantity_required
                FROM RECIPE_INGREDIENT ri
                JOIN INGREDIENT i ON ri.ingredient_id = i.ingredient_id
                WHERE ri.plan_id = %s
            """, (plan_id,))
            
            recipe_ingredients = cursor.fetchall()
            
            print("\n--- Required Ingredients ---")
            ingredient_list = []
            
            for ing in recipe_ingredients:
                total_needed = ing['quantity_required'] * produced_units
                print(f"\n{ing['name']}: {total_needed} oz needed")
                
                # Show available batches for this ingredient
                cursor.execute("""
                    SELECT ib.lot_number, ib.on_hand_oz, ib.expiration_date
                    FROM INGREDIENT_BATCH ib
                    WHERE ib.ingredient_id = %s 
                      AND ib.manufacturer_id = %s
                      AND ib.on_hand_oz > 0
                      AND ib.expiration_date > CURRENT_DATE
                    ORDER BY ib.expiration_date
                """, (ing['ingredient_id'], self.manufacturer_id))
                
                batches = cursor.fetchall()
                
                if not batches:
                    print(f"  ✗ No available batches for {ing['name']}")
                    return
                
                print("  Available batches:")
                for b in batches:
                    print(f"    {b['lot_number']}: {b['on_hand_oz']} oz (exp: {b['expiration_date']})")
                
                lot = input(f"  Select lot number: ").strip()
                qty = float(input(f"  Quantity to use: ").strip())
                
                ingredient_list.append({
                    'lot': lot,
                    'qty': qty
                })
            
            # Call stored procedure
            ingredient_json = json.dumps(ingredient_list)
            
            cursor.callproc('RecordProductionBatch', [
                product_id,
                plan_id,
                self.manufacturer_id,
                batch_id,
                produced_units,
                ingredient_json
            ])
            
            # Fetch results
            for result in cursor.stored_results():
                data = result.fetchone()
                if data:
                    print(f"\n✓ Product batch created successfully!")
                    print(f"   Lot Number: {data['product_lot']}")
                    print(f"   Units Produced: {data['produced_units']}")
                    print(f"   Total Cost: ${data['batch_total_cost']:.2f}")
                    print(f"   Per Unit Cost: ${data['unit_cost']:.4f}")
            
            connection.commit()
            
        except Exception as e:
            connection.rollback()
            print(f"\n✗ Error creating product batch: {e}")
        finally:
            cursor.close()
    
    def reports_menu(self):
        """Display reports submenu"""
        while True:
            print(f"\n{'='*50}")
            print("  REPORTS MENU")
            print(f"{'='*50}")
            print("1. On-hand by item/lot")
            print("2. Nearly-out-of-stock")
            print("3. Almost-expired ingredient lots")
            print("4. Batch Cost Summary")
            print("5. Back")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                self.report_on_hand()
            elif choice == '2':
                self.report_nearly_out_of_stock()
            elif choice == '3':
                self.report_almost_expired()
            elif choice == '4':
                self.report_batch_cost()
            elif choice == '5':
                break
            else:
                print("\nInvalid choice.")
    
    def report_on_hand(self):
        """Report: On-hand by item/lot"""
        print("\n=== ON-HAND INVENTORY ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    ib.lot_number,
                    i.name AS ingredient_name,
                    ib.on_hand_oz,
                    ib.expiration_date
                FROM INGREDIENT_BATCH ib
                JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
                WHERE ib.manufacturer_id = %s AND ib.on_hand_oz > 0
                ORDER BY i.name, ib.expiration_date
            """, (self.manufacturer_id,))
            
            results = cursor.fetchall()
            
            if not results:
                print("\nNo inventory on hand.")
                return
            
            print(f"\n{'Lot Number':<20} {'Ingredient':<30} {'On Hand (oz)':<15} {'Expiration'}")
            print("-" * 90)
            
            for row in results:
                print(f"{row['lot_number']:<20} {row['ingredient_name']:<30} "
                      f"{row['on_hand_oz']:<15.2f} {row['expiration_date']}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def report_nearly_out_of_stock(self):
        """Report: Nearly-out-of-stock products"""
        print("\n=== NEARLY OUT OF STOCK ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    p.product_id,
                    p.name,
                    p.standard_batch_size,
                    COALESCE(SUM(pb.quantity_produced), 0) AS total_on_hand
                FROM PRODUCT p
                LEFT JOIN PRODUCT_BATCH pb ON p.product_id = pb.product_id
                WHERE p.manufacturer_id = %s
                GROUP BY p.product_id, p.name, p.standard_batch_size
                HAVING total_on_hand < p.standard_batch_size
                ORDER BY p.name
            """, (self.manufacturer_id,))
            
            results = cursor.fetchall()
            
            if not results:
                print("\nAll products adequately stocked!")
                return
            
            print(f"\n{'Product ID':<12} {'Product Name':<30} {'Standard Size':<15} {'On Hand'}")
            print("-" * 80)
            
            for row in results:
                print(f"{row['product_id']:<12} {row['name']:<30} "
                      f"{row['standard_batch_size']:<15} {row['total_on_hand']}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def report_almost_expired(self):
        """Report: Almost-expired ingredient lots (within 10 days)"""
        print("\n=== ALMOST-EXPIRED INGREDIENTS ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    ib.lot_number,
                    i.name AS ingredient_name,
                    ib.on_hand_oz,
                    ib.expiration_date,
                    DATEDIFF(ib.expiration_date, CURRENT_DATE) AS days_until_expiry
                FROM INGREDIENT_BATCH ib
                JOIN INGREDIENT i ON ib.ingredient_id = i.ingredient_id
                WHERE ib.manufacturer_id = %s
                  AND ib.expiration_date <= DATE_ADD(CURRENT_DATE, INTERVAL 10 DAY)
                  AND ib.on_hand_oz > 0
                ORDER BY ib.expiration_date
            """, (self.manufacturer_id,))
            
            results = cursor.fetchall()
            
            if not results:
                print("\nNo ingredients expiring within 10 days.")
                return
            
            print(f"\n{'Lot Number':<20} {'Ingredient':<30} {'On Hand':<12} {'Exp Date':<12} {'Days Left'}")
            print("-" * 95)
            
            for row in results:
                print(f"{row['lot_number']:<20} {row['ingredient_name']:<30} "
                      f"{row['on_hand_oz']:<12.2f} {row['expiration_date']!s:<12} {row['days_until_expiry']}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def report_batch_cost(self):
        """Report: Batch cost summary for a specific product batch"""
        print("\n=== BATCH COST SUMMARY ===")
        
        lot_number = input("Enter product batch lot number: ").strip()
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    pb.lot_number,
                    p.name AS product_name,
                    pb.quantity_produced,
                    pb.total_cost,
                    pb.per_unit_cost,
                    pb.production_date
                FROM PRODUCT_BATCH pb
                JOIN PRODUCT p ON pb.product_id = p.product_id
                WHERE pb.lot_number = %s AND pb.manufacturer_id = %s
            """, (lot_number, self.manufacturer_id))
            
            result = cursor.fetchone()
            
            if not result:
                print("\nBatch not found.")
                return
            
            print(f"\nProduct: {result['product_name']}")
            print(f"Lot Number: {result['lot_number']}")
            print(f"Production Date: {result['production_date']}")
            print(f"Units Produced: {result['quantity_produced']}")
            print(f"Total Cost: ${result['total_cost']:.2f}")
            print(f"Per Unit Cost: ${result['per_unit_cost']:.4f}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def execute_queries(self):
        """Execute required retrieval queries"""
        from query_executor import QueryExecutor
        executor = QueryExecutor(self.db)
        executor.display_menu()