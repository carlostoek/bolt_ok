-- Shop Categories Migration SQL
-- Creates shop_categories table and populates with default categories
-- for existing shop items migration

-- Create shop_categories table if it doesn't exist
CREATE TABLE IF NOT EXISTS shop_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    is_vip_only BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create unique index on name to prevent duplicates
CREATE UNIQUE INDEX IF NOT EXISTS idx_shop_categories_name ON shop_categories(name);

-- Create index for display ordering
CREATE INDEX IF NOT EXISTS idx_shop_categories_display_order ON shop_categories(display_order, is_active);

-- Insert default categories for existing items migration
INSERT OR IGNORE INTO shop_categories (name, description, display_order, is_active, is_vip_only)
VALUES
    ('Objetos Personales', 'Artículos íntimos y personales de Diana y Lucien', 1, 1, 0),
    ('Recuerdos del Pasado', 'Memorias y objetos que revelan historias del pasado', 2, 1, 0),
    ('Colección VIP', 'Artículos exclusivos solo para miembros VIP', 3, 1, 1),
    ('Experiencias Especiales', 'Momentos únicos y experiencias narrativas', 4, 1, 0),
    ('Pistas y Secretos', 'Objetos que desbloquean lore y secretos de la historia', 5, 1, 0);

-- Update existing shop_items to assign default categories if they don't have one
-- This ensures existing items are properly categorized after migration

-- Update items that match diary/personal content to "Objetos Personales"
UPDATE shop_items
SET category_id = (SELECT id FROM shop_categories WHERE name = 'Objetos Personales')
WHERE category_id IS NULL
  AND (LOWER(name) LIKE '%diario%' OR LOWER(description) LIKE '%personal%' OR LOWER(description) LIKE '%íntim%');

-- Update items that reference memories/past to "Recuerdos del Pasado"
UPDATE shop_items
SET category_id = (SELECT id FROM shop_categories WHERE name = 'Recuerdos del Pasado')
WHERE category_id IS NULL
  AND (LOWER(name) LIKE '%cofre%' OR LOWER(name) LIKE '%recuerdo%' OR LOWER(description) LIKE '%pasado%' OR LOWER(description) LIKE '%carta%' OR LOWER(description) LIKE '%foto%');

-- Update VIP-only items to "Colección VIP"
UPDATE shop_items
SET category_id = (SELECT id FROM shop_categories WHERE name = 'Colección VIP')
WHERE category_id IS NULL
  AND is_vip_only = 1;

-- Update items that reference special moments to "Experiencias Especiales"
UPDATE shop_items
SET category_id = (SELECT id FROM shop_categories WHERE name = 'Experiencias Especiales')
WHERE category_id IS NULL
  AND (LOWER(name) LIKE '%máscara%' OR LOWER(name) LIKE '%baile%' OR LOWER(description) LIKE '%cita%' OR LOWER(description) LIKE '%momento%');

-- Update any remaining items that unlock lore pieces to "Pistas y Secretos"
UPDATE shop_items
SET category_id = (SELECT id FROM shop_categories WHERE name = 'Pistas y Secretos')
WHERE category_id IS NULL
  AND unlocks_lore_piece_id IS NOT NULL;

-- For any remaining uncategorized items, assign them to "Objetos Personales" as default
UPDATE shop_items
SET category_id = (SELECT id FROM shop_categories WHERE name = 'Objetos Personales')
WHERE category_id IS NULL;

-- Add foreign key constraint to shop_items.category_id if the column exists
-- Note: SQLite requires recreating table to add FK constraints, but since this is already
-- defined in the model, we just ensure the index exists for performance
CREATE INDEX IF NOT EXISTS idx_shop_items_category_id ON shop_items(category_id);