"""
Database migration script to add enhanced document management fields
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add enhanced document management fields to the database"""
    
    # Database path
    db_path = 'instance/law_firm.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting database migration for enhanced document management...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(document)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = {
            'is_template': 'BOOLEAN DEFAULT 0',
            'template_details': 'TEXT',
            'retention_policy_id': 'INTEGER',
            'expiry_date': 'DATETIME',
            'ocr_processed': 'BOOLEAN DEFAULT 0',
            'ocr_error': 'TEXT',
            'search_vector': 'TEXT',
            'checksum': 'VARCHAR(64)',
            'metadata': 'TEXT',
            'last_accessed': 'DATETIME',
            'access_count': 'INTEGER DEFAULT 0'
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE document ADD COLUMN {column_name} {column_type}")
            else:
                print(f"Column {column_name} already exists")
        
        # Create indexes for better performance
        indexes = [
            ("idx_document_ocr_processed", "CREATE INDEX IF NOT EXISTS idx_document_ocr_processed ON document (ocr_processed)"),
            ("idx_document_expiry_date", "CREATE INDEX IF NOT EXISTS idx_document_expiry_date ON document (expiry_date)"),
            ("idx_document_is_template", "CREATE INDEX IF NOT EXISTS idx_document_is_template ON document (is_template)"),
            ("idx_document_last_accessed", "CREATE INDEX IF NOT EXISTS idx_document_last_accessed ON document (last_accessed)")
        ]
        
        for index_name, index_sql in indexes:
            print(f"Creating index: {index_name}")
            cursor.execute(index_sql)
        
        # Commit changes
        conn.commit()
        print("Database migration completed successfully!")
        
        # Close connection
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    migrate_database()