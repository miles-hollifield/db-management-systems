"""
Database Connection Module
Handles MySQL database connections using mysql-connector-python
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    """Manages database connection for the application"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            # Database configuration
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '3306')),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'inventory_db'),
                autocommit=False
            )
            
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print(f"Successfully connected to MySQL Server version {db_info}")
                
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise
    
    def get_connection(self):
        """Return the active connection"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection
    
    def close(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed.")
    
    def commit(self):
        """Commit current transaction"""
        if self.connection:
            self.connection.commit()
    
    def rollback(self):
        """Rollback current transaction"""
        if self.connection:
            self.connection.rollback()
    
    def execute_query(self, query, params=None, fetch=True):
        """
        Execute a SQL query with optional parameters
        
        Args:
            query (str): SQL query to execute
            params (tuple): Query parameters
            fetch (bool): Whether to fetch results
            
        Returns:
            list: Query results if fetch=True, None otherwise
        """
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.lastrowid
                
        except Error as e:
            self.connection.rollback()
            print(f"Query execution error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def call_procedure(self, procedure_name, params):
        """
        Call a stored procedure
        
        Args:
            procedure_name (str): Name of the stored procedure
            params (tuple): Procedure parameters
            
        Returns:
            list: Procedure results
        """
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.callproc(procedure_name, params)
            
            # Fetch results from all result sets
            results = []
            for result in cursor.stored_results():
                results.extend(result.fetchall())
            
            self.connection.commit()
            return results
            
        except Error as e:
            self.connection.rollback()
            print(f"Procedure execution error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()