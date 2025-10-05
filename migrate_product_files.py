"""
Migration script to add product_files table.
"""
import logging
from sqlalchemy import text, create_engine
from database.setup import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_product_files():
    """Create the product_files table if it doesn't exist."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Check if table exists
            check_table_sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'product_files'
            );
            """
            result = conn.execute(text(check_table_sql))
            table_exists = result.scalar()
            
            if not table_exists:
                # Create the product_files table
                create_table_sql = """
                CREATE TABLE product_files (
                    id SERIAL PRIMARY KEY,
                    shop_item_id INTEGER NOT NULL REFERENCES shop_items(id) ON DELETE CASCADE,
                    file_type VARCHAR(20) NOT NULL,
                    file_id VARCHAR(255) NOT NULL,
                    order_index INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                conn.execute(text(create_table_sql))
                conn.commit()
                logger.info("✅ Created product_files table")
            else:
                logger.info("✅ product_files table already exists")
                
        except Exception as e:
            logger.error(f"❌ Error creating product_files table: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_product_files()
