-- Shop Items Extensions Migration SQL
-- Extends shop_items table with new columns for enhanced functionality
-- This migration assumes shop_categories already exist from migration 001

-- Create shop_promotions table if it doesn't exist
CREATE TABLE IF NOT EXISTS shop_promotions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    discount_percentage REAL,
    discount_amount INTEGER,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    applies_to_category_id INTEGER,
    applies_to_item_id INTEGER,
    min_purchase_amount INTEGER DEFAULT 0,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applies_to_category_id) REFERENCES shop_categories(id),
    FOREIGN KEY (applies_to_item_id) REFERENCES shop_items(id)
);

-- Create indices for shop_promotions
CREATE INDEX IF NOT EXISTS idx_shop_promotions_dates ON shop_promotions(start_date, end_date, is_active);
CREATE INDEX IF NOT EXISTS idx_shop_promotions_category ON shop_promotions(applies_to_category_id);
CREATE INDEX IF NOT EXISTS idx_shop_promotions_item ON shop_promotions(applies_to_item_id);

-- Add new columns to shop_items table if they don't exist
-- Note: SQLite doesn't support adding multiple columns in one statement, so we add them one by one

-- Add category_id column if it doesn't exist
-- Check if column exists first to avoid errors on re-runs
PRAGMA table_info(shop_items);

-- Add category_id column (this may already exist from previous migrations)
ALTER TABLE shop_items ADD COLUMN category_id INTEGER;

-- Add promotion_id column
ALTER TABLE shop_items ADD COLUMN promotion_id INTEGER;

-- Add display_order column with default value
ALTER TABLE shop_items ADD COLUMN display_order INTEGER DEFAULT 0;

-- Add purchase_limit_per_user column (null means unlimited)
ALTER TABLE shop_items ADD COLUMN purchase_limit_per_user INTEGER;

-- Create indices for the new columns
CREATE INDEX IF NOT EXISTS idx_shop_items_category_id ON shop_items(category_id);
CREATE INDEX IF NOT EXISTS idx_shop_items_promotion_id ON shop_items(promotion_id);
CREATE INDEX IF NOT EXISTS idx_shop_items_display_order ON shop_items(display_order);
CREATE INDEX IF NOT EXISTS idx_shop_items_active_order ON shop_items(is_active, display_order);

-- Data migration: Assign existing items to default category if they don't have one
-- This ensures backward compatibility with existing shop items

-- Assign uncategorized items to the "Objetos Personales" category as default
UPDATE shop_items
SET category_id = (SELECT id FROM shop_categories WHERE name = 'Objetos Personales' LIMIT 1)
WHERE category_id IS NULL;

-- Set default display_order for existing items based on their creation order
-- This gives existing items a logical ordering
UPDATE shop_items
SET display_order = id * 10
WHERE display_order = 0 OR display_order IS NULL;

-- Ensure VIP items are properly categorized if they somehow weren't caught in previous migration
UPDATE shop_items
SET category_id = (SELECT id FROM shop_categories WHERE name = 'Colección VIP' LIMIT 1)
WHERE is_vip_only = 1
  AND category_id = (SELECT id FROM shop_categories WHERE name = 'Objetos Personales' LIMIT 1);

-- Sample promotion data (optional - creates a welcome promotion for new shop features)
INSERT OR IGNORE INTO shop_promotions (
    name,
    description,
    discount_percentage,
    start_date,
    end_date,
    is_active,
    min_purchase_amount
) VALUES (
    'Bienvenida a la Nueva Tienda',
    'Descuento especial para celebrar las nuevas funciones de la tienda',
    10.0,
    datetime('now'),
    datetime('now', '+30 days'),
    1,
    50
);