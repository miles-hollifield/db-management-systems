"""
CSC440 Project: Inventory Management System
Main Application File

Team Members:
- Miles Hollifield (mfhollif)
- Claire Jeffries (cmjeffri)
"""

import sys
from database_connection import DatabaseConnection
from manufacturer_menu import ManufacturerMenu
from supplier_menu import SupplierMenu
from viewer_menu import ViewerMenu


class InventoryManagementSystem:
    def __init__(self):
        self.db_connection = DatabaseConnection()
        self.current_user = None
        self.current_role = None
        
    def display_welcome(self):
        """Display welcome banner"""
        print("\n" + "="*50)
        print("  INVENTORY MANAGEMENT SYSTEM")
        print("  Prepared/Frozen Meals Manufacturer")
        print("="*50)
        
    def login_screen(self):
        """Display login/role selection screen"""
        while True:
            print("\n=== LOGIN / ROLE SELECTION ===")
            print("1. Manufacturer")
            print("2. Supplier")
            print("3. Viewer")
            print("4. Exit")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                return self.manufacturer_login()
            elif choice == '2':
                return self.supplier_login()
            elif choice == '3':
                return self.viewer_login()
            elif choice == '4':
                print("\nThank you for using the Inventory Management System!")
                return None
            else:
                print("\nInvalid choice. Please try again.")
    
    def manufacturer_login(self):
        """Handle manufacturer login"""
        print("\n=== MANUFACTURER LOGIN ===")
        username = input("Username: ").strip()
        # In production, you'd verify password. For this project, simplified authentication
        
        connection = self.db_connection.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Verify user exists and has MANUFACTURER role
            cursor.execute("""
                SELECT u.user_id, u.username, u.role, m.manufacturer_id, m.name
                FROM USER u
                JOIN MANUFACTURER m ON u.user_id = m.user_id
                WHERE u.username = %s AND u.role = 'MANUFACTURER'
            """, (username,))
            
            user = cursor.fetchone()
            
            if user:
                self.current_user = user
                self.current_role = 'MANUFACTURER'
                print(f"\nWelcome, {user['name']} (ID: {user['manufacturer_id']})")
                return True
            else:
                print("\nInvalid username or not a manufacturer account.")
                return False
                
        except Exception as e:
            print(f"\nLogin error: {e}")
            return False
        finally:
            cursor.close()
    
    def supplier_login(self):
        """Handle supplier login"""
        print("\n=== SUPPLIER LOGIN ===")
        username = input("Username: ").strip()
        
        connection = self.db_connection.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT u.user_id, u.username, u.role, s.supplier_id, s.name
                FROM USER u
                JOIN SUPPLIER s ON u.user_id = s.user_id
                WHERE u.username = %s AND u.role = 'SUPPLIER'
            """, (username,))
            
            user = cursor.fetchone()
            
            if user:
                self.current_user = user
                self.current_role = 'SUPPLIER'
                print(f"\nWelcome, {user['name']} (ID: {user['supplier_id']})")
                return True
            else:
                print("\nInvalid username or not a supplier account.")
                return False
                
        except Exception as e:
            print(f"\nLogin error: {e}")
            return False
        finally:
            cursor.close()
    
    def viewer_login(self):
        """Handle viewer login"""
        print("\n=== VIEWER LOGIN ===")
        username = input("Username: ").strip()
        
        connection = self.db_connection.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT user_id, username, role
                FROM USER
                WHERE username = %s AND role = 'VIEWER'
            """, (username,))
            
            user = cursor.fetchone()
            
            if user:
                self.current_user = user
                self.current_role = 'VIEWER'
                print(f"\nWelcome, {user['username']}")
                return True
            else:
                print("\nInvalid username or not a viewer account.")
                return False
                
        except Exception as e:
            print(f"\nLogin error: {e}")
            return False
        finally:
            cursor.close()
    
    def run(self):
        """Main application loop"""
        self.display_welcome()
        
        try:
            while True:
                # Login screen
                if not self.login_screen():
                    break
                
                # Route to appropriate menu based on role
                if self.current_role == 'MANUFACTURER':
                    manufacturer_menu = ManufacturerMenu(
                        self.db_connection, 
                        self.current_user
                    )
                    manufacturer_menu.display_menu()
                    
                elif self.current_role == 'SUPPLIER':
                    supplier_menu = SupplierMenu(
                        self.db_connection,
                        self.current_user
                    )
                    supplier_menu.display_menu()
                    
                elif self.current_role == 'VIEWER':
                    viewer_menu = ViewerMenu(self.db_connection)
                    viewer_menu.display_menu()
                
                # Reset current user after logout
                self.current_user = None
                self.current_role = None
                
        except KeyboardInterrupt:
            print("\n\nApplication interrupted by user.")
        except Exception as e:
            print(f"\n\nUnexpected error: {e}")
        finally:
            self.db_connection.close()
            print("\nDatabase connection closed. Goodbye!")


def main():
    """Application entry point"""
    app = InventoryManagementSystem()
    app.run()


if __name__ == "__main__":
    main()