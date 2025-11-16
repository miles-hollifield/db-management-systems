"""
Supplier Menu Module
Handles all supplier-specific operations
"""


class SupplierMenu:
    def __init__(self, db_connection, user):
        self.db = db_connection
        self.user = user
        self.supplier_id = user['supplier_id']
        
    def display_menu(self):
        """Display supplier menu and handle choices"""
        while True:
            print(f"\n{'='*50}")
            print(f"  SUPPLIER MENU - {self.user['name']}")
            print(f"{'='*50}")
            print("1. Manage Ingredients Supplied")
            print("2. Define/Update Ingredient")
            print("3. Create Ingredient Batch")
            print("4. Execute Queries")
            print("5. Logout")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                self.view_ingredients_supplied()
            elif choice == '2':
                self.define_ingredient()
            elif choice == '3':
                self.create_ingredient_batch()
            elif choice == '4':
                self.execute_queries()
            elif choice == '5':
                print("\nLogging out...")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def view_ingredients_supplied(self):
        """View all ingredients this supplier provides"""
        print("\n=== INGREDIENTS SUPPLIED ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT i.ingredient_id, i.name, i.type
                FROM INGREDIENT i
                WHERE i.supplier_id = %s
                ORDER BY i.name
            """, (self.supplier_id,))
            
            ingredients = cursor.fetchall()
            
            if not ingredients:
                print("\nNo ingredients found. Define ingredients first.")
                return
            
            print(f"\n{'ID':<8} {'Name':<40} {'Type'}")
            print("-" * 60)
            
            for ing in ingredients:
                print(f"{ing['ingredient_id']:<8} {ing['name']:<40} {ing['type']}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
        finally:
            cursor.close()
    
    def define_ingredient(self):
        """Define a new ingredient (atomic or compound)"""
        print("\n=== DEFINE INGREDIENT ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Get ingredient details
            name = input("Ingredient name: ").strip()
            print("\nIngredient Type:")
            print("1. ATOMIC")
            print("2. COMPOUND")
            type_choice = input("Select type (1-2): ").strip()
            
            ingredient_type = 'ATOMIC' if type_choice == '1' else 'COMPOUND'
            
            # Insert ingredient
            cursor.execute("""
                INSERT INTO INGREDIENT (supplier_id, name, type)
                VALUES (%s, %s, %s)
            """, (self.supplier_id, name, ingredient_type))
            
            ingredient_id = cursor.lastrowid
            
            print(f"\n✓ Ingredient created! ID: {ingredient_id}")
            
            # Create formulation (pricing information)
            print("\n--- Define Formulation ---")
            pack_size = float(input("Pack size (units): ").strip())
            unit_price = float(input("Unit price per pack: ").strip())
            effective_start = input("Effective start date (YYYY-MM-DD): ").strip()
            effective_end = input("Effective end date (YYYY-MM-DD or press Enter for NULL): ").strip()
            
            if not effective_end:
                effective_end = None
            
            cursor.execute("""
                INSERT INTO FORMULATION 
                (ingredient_id, pack_size, unit_price, effective_start_date, effective_end_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (ingredient_id, pack_size, unit_price, effective_start, effective_end))
            
            formulation_id = cursor.lastrowid
            
            print(f"✓ Formulation created! ID: {formulation_id}")
            
            # If compound, add materials
            if ingredient_type == 'COMPOUND':
                print("\n--- Add Materials to Compound Ingredient ---")
                print("Note: Materials must be ATOMIC ingredients")
                
                while True:
                    # Show available atomic ingredients
                    cursor.execute("""
                        SELECT ingredient_id, name, supplier_id, type
                        FROM INGREDIENT
                        WHERE type = 'ATOMIC'
                        ORDER BY name
                        LIMIT 20
                    """)
                    
                    materials = cursor.fetchall()
                    
                    print("\nAvailable Atomic Ingredients (showing first 20):")
                    for mat in materials:
                        supplier_name = f"(Supplier {mat['supplier_id']})"
                        print(f"{mat['ingredient_id']}. {mat['name']} {supplier_name}")
                    
                    material_id = input("\nMaterial ingredient ID (or 'done' to finish): ").strip()
                    
                    if material_id.lower() == 'done':
                        break
                    
                    quantity = float(input("Quantity required (ounces): ").strip())
                    
                    cursor.execute("""
                        INSERT INTO FORMULATION_MATERIAL 
                        (formulation_id, material_ingredient_id, quantity_required)
                        VALUES (%s, %s, %s)
                    """, (formulation_id, int(material_id), quantity))
                    
                    print("✓ Material added")
            
            connection.commit()
            print(f"\n✓ Ingredient fully defined!")
            
        except Exception as e:
            connection.rollback()
            print(f"\n✗ Error defining ingredient: {e}")
        finally:
            cursor.close()
    
    def create_ingredient_batch(self):
        """Create an ingredient batch (supplier intake)"""
        print("\n=== CREATE INGREDIENT BATCH ===")
        
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Show supplier's ingredients
            cursor.execute("""
                SELECT ingredient_id, name, type
                FROM INGREDIENT
                WHERE supplier_id = %s
                ORDER BY name
            """, (self.supplier_id,))
            
            ingredients = cursor.fetchall()
            
            if not ingredients:
                print("\nNo ingredients defined. Define an ingredient first.")
                return
            
            print("\nYour Ingredients:")
            for ing in ingredients:
                print(f"{ing['ingredient_id']}. {ing['name']} ({ing['type']})")
            
            # Get batch details
            ingredient_id = int(input("\nSelect Ingredient ID: ").strip())
            
            # Verify ingredient belongs to this supplier
            if not any(ing['ingredient_id'] == ingredient_id for ing in ingredients):
                print("\n✗ Invalid ingredient ID for this supplier.")
                return
            
            batch_id = input("Batch ID: ").strip()
            quantity = float(input("Quantity (ounces): ").strip())
            cost_per_unit = float(input("Cost per unit: ").strip())
            expiration_date = input("Expiration date (YYYY-MM-DD): ").strip()
            
            # Insert ingredient batch (manufacturer_id is NULL for supplier-created batches)
            cursor.execute("""
                INSERT INTO INGREDIENT_BATCH 
                (ingredient_id, supplier_id, manufacturer_id, batch_id, quantity, 
                 cost_per_unit, expiration_date, received_date)
                VALUES (%s, %s, NULL, %s, %s, %s, %s, CURRENT_DATE)
            """, (ingredient_id, self.supplier_id, batch_id, quantity, 
                  cost_per_unit, expiration_date))
            
            connection.commit()
            
            # Get the generated lot number
            cursor.execute("""
                SELECT lot_number 
                FROM INGREDIENT_BATCH 
                WHERE ingredient_id = %s AND supplier_id = %s AND batch_id = %s
            """, (ingredient_id, self.supplier_id, batch_id))
            
            result = cursor.fetchone()
            lot_number = result['lot_number'] if result else 'Unknown'
            
            print(f"\n✓ Ingredient batch created successfully!")
            print(f"   Lot Number: {lot_number}")
            print(f"   Available for manufacturers to receive")
            
        except Exception as e:
            connection.rollback()
            print(f"\n✗ Error creating ingredient batch: {e}")
        finally:
            cursor.close()
    
    def execute_queries(self):
        """Execute required retrieval queries"""
        from query_executor import QueryExecutor
        executor = QueryExecutor(self.db)
        executor.display_menu()