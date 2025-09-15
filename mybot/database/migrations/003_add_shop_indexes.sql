-- Shop Performance Indexes Migration SQL
-- Creates comprehensive indexes for shop queries to optimize performance
-- Based on common query patterns in ShopService and expected admin operations

-- ========================================
-- SHOP ITEMS PERFORMANCE INDEXES
-- ========================================

-- Composite index for active items filtering with VIP consideration
-- Optimizes: WHERE is_active = 1 AND is_vip_only = 0/1 ORDER BY display_order
CREATE INDEX IF NOT EXISTS idx_shop_items_active_vip_order ON shop_items(is_active, is_vip_only, display_order);

-- Category-based filtering with activity status
-- Optimizes: WHERE category_id = X AND is_active = 1 ORDER BY display_order
CREATE INDEX IF NOT EXISTS idx_shop_items_category_active_order ON shop_items(category_id, is_active, display_order);

-- Price-based queries for filtering and sorting
-- Optimizes: WHERE is_active = 1 ORDER BY price
CREATE INDEX IF NOT EXISTS idx_shop_items_active_price ON shop_items(is_active, price);

-- VIP items with lore unlocking
-- Optimizes: WHERE is_vip_only = 1 AND unlocks_lore_piece_id IS NOT NULL
CREATE INDEX IF NOT EXISTS idx_shop_items_vip_lore ON shop_items(is_vip_only, unlocks_lore_piece_id);

-- Active items with purchase limits (for admin management)
-- Optimizes: WHERE is_active = 1 AND purchase_limit_per_user IS NOT NULL
CREATE INDEX IF NOT EXISTS idx_shop_items_active_limited ON shop_items(is_active, purchase_limit_per_user);

-- ========================================
-- USER PURCHASES PERFORMANCE INDEXES
-- ========================================

-- Primary user purchase lookup
-- Optimizes: WHERE user_id = X ORDER BY purchased_at DESC
CREATE INDEX IF NOT EXISTS idx_user_purchases_user_date ON user_purchases(user_id, purchased_at DESC);

-- Item purchase history
-- Optimizes: WHERE shop_item_id = X ORDER BY purchased_at DESC
CREATE INDEX IF NOT EXISTS idx_user_purchases_item_date ON user_purchases(shop_item_id, purchased_at DESC);

-- User-item combination for ownership checks
-- Optimizes: WHERE user_id = X AND shop_item_id = Y
CREATE INDEX IF NOT EXISTS idx_user_purchases_user_item ON user_purchases(user_id, shop_item_id);

-- Purchase analytics by price range
-- Optimizes: WHERE price_paid BETWEEN X AND Y ORDER BY purchased_at
CREATE INDEX IF NOT EXISTS idx_user_purchases_price_date ON user_purchases(price_paid, purchased_at);

-- Recent purchases for admin monitoring
-- Optimizes: ORDER BY purchased_at DESC LIMIT X
CREATE INDEX IF NOT EXISTS idx_user_purchases_recent ON user_purchases(purchased_at DESC);

-- ========================================
-- SHOP CATEGORIES PERFORMANCE INDEXES
-- ========================================

-- Active categories ordered by display
-- Optimizes: WHERE is_active = 1 ORDER BY display_order
CREATE INDEX IF NOT EXISTS idx_shop_categories_active_order ON shop_categories(is_active, display_order);

-- VIP category filtering
-- Optimizes: WHERE is_vip_only = 1 AND is_active = 1
CREATE INDEX IF NOT EXISTS idx_shop_categories_vip_active ON shop_categories(is_vip_only, is_active);

-- Category name lookup (already exists as unique index, but covering for completeness)
-- Optimizes: WHERE name = 'category_name'
-- Note: This already exists from migration 001 as idx_shop_categories_name

-- ========================================
-- SHOP PROMOTIONS PERFORMANCE INDEXES
-- ========================================

-- Active promotions within date range
-- Optimizes: WHERE is_active = 1 AND start_date <= NOW() AND end_date >= NOW()
CREATE INDEX IF NOT EXISTS idx_shop_promotions_active_period ON shop_promotions(is_active, start_date, end_date);

-- Category-specific promotions
-- Optimizes: WHERE applies_to_category_id = X AND is_active = 1
CREATE INDEX IF NOT EXISTS idx_shop_promotions_category_active ON shop_promotions(applies_to_category_id, is_active);

-- Item-specific promotions
-- Optimizes: WHERE applies_to_item_id = X AND is_active = 1
CREATE INDEX IF NOT EXISTS idx_shop_promotions_item_active ON shop_promotions(applies_to_item_id, is_active);

-- Usage tracking for promotion limits
-- Optimizes: WHERE max_uses IS NOT NULL AND current_uses < max_uses
CREATE INDEX IF NOT EXISTS idx_shop_promotions_usage ON shop_promotions(max_uses, current_uses, is_active);

-- ========================================
-- LORE PIECES INTEGRATION INDEXES
-- ========================================

-- Shop items with lore pieces lookup
-- Optimizes: JOIN lore_pieces ON shop_items.unlocks_lore_piece_id = lore_pieces.id
CREATE INDEX IF NOT EXISTS idx_lore_pieces_shop_integration ON lore_pieces(id, is_active);

-- User lore pieces for backpack queries
-- Optimizes: WHERE user_id = X ORDER BY unlocked_at DESC
CREATE INDEX IF NOT EXISTS idx_user_lore_pieces_user_date ON user_lore_pieces(user_id, unlocked_at DESC);

-- Lore piece ownership check
-- Optimizes: WHERE user_id = X AND lore_piece_id = Y
CREATE INDEX IF NOT EXISTS idx_user_lore_pieces_user_piece ON user_lore_pieces(user_id, lore_piece_id);

-- ========================================
-- ANALYTICS AND REPORTING INDEXES
-- ========================================

-- Daily sales analytics
-- Optimizes: SELECT DATE(purchased_at), COUNT(*), SUM(price_paid) FROM user_purchases GROUP BY DATE(purchased_at)
CREATE INDEX IF NOT EXISTS idx_user_purchases_date_analytics ON user_purchases(DATE(purchased_at), price_paid);

-- Popular items analytics
-- Optimizes: SELECT shop_item_id, COUNT(*) FROM user_purchases GROUP BY shop_item_id
CREATE INDEX IF NOT EXISTS idx_user_purchases_item_analytics ON user_purchases(shop_item_id, purchased_at);

-- User spending analytics
-- Optimizes: SELECT user_id, SUM(price_paid) FROM user_purchases GROUP BY user_id
CREATE INDEX IF NOT EXISTS idx_user_purchases_user_spending ON user_purchases(user_id, price_paid);

-- ========================================
-- COMPOUND BUSINESS LOGIC INDEXES
-- ========================================

-- Complete shop listing optimization (most common query)
-- Optimizes: Complex queries with category, VIP, active status, and ordering
CREATE INDEX IF NOT EXISTS idx_shop_items_full_listing ON shop_items(
    is_active,
    category_id,
    is_vip_only,
    display_order,
    price
);

-- Purchase limit enforcement
-- Optimizes: Checking user purchase count against item limits
CREATE INDEX IF NOT EXISTS idx_user_purchases_limit_check ON user_purchases(
    user_id,
    shop_item_id,
    purchased_at
);

-- Promotion eligibility checking
-- Optimizes: Complex promotion validation queries
CREATE INDEX IF NOT EXISTS idx_shop_promotions_eligibility ON shop_promotions(
    is_active,
    start_date,
    end_date,
    applies_to_category_id,
    applies_to_item_id,
    min_purchase_amount
);

-- ========================================
-- CLEANUP AND MAINTENANCE INDEXES
-- ========================================

-- Expired promotions cleanup
-- Optimizes: WHERE end_date < NOW() AND is_active = 1
CREATE INDEX IF NOT EXISTS idx_shop_promotions_expired ON shop_promotions(end_date, is_active);

-- Inactive items cleanup queries
-- Optimizes: WHERE is_active = 0 AND updated_at < DATE_SUB(NOW(), INTERVAL X MONTH)
CREATE INDEX IF NOT EXISTS idx_shop_items_inactive ON shop_items(is_active, created_at);

-- Old purchase records archival
-- Optimizes: WHERE purchased_at < DATE_SUB(NOW(), INTERVAL X YEAR)
CREATE INDEX IF NOT EXISTS idx_user_purchases_archival ON user_purchases(purchased_at);

-- ========================================
-- FOREIGN KEY OPTIMIZATION INDEXES
-- ========================================

-- These indexes optimize foreign key constraint checks and cascading operations
-- Many of these may already exist from previous migrations, using IF NOT EXISTS for safety

-- Shop items to categories relationship
CREATE INDEX IF NOT EXISTS idx_shop_items_fk_category ON shop_items(category_id);

-- Shop items to promotions relationship
CREATE INDEX IF NOT EXISTS idx_shop_items_fk_promotion ON shop_items(promotion_id);

-- Shop items to lore pieces relationship
CREATE INDEX IF NOT EXISTS idx_shop_items_fk_lore ON shop_items(unlocks_lore_piece_id);

-- User purchases to users relationship
CREATE INDEX IF NOT EXISTS idx_user_purchases_fk_user ON user_purchases(user_id);

-- User purchases to shop items relationship
CREATE INDEX IF NOT EXISTS idx_user_purchases_fk_item ON user_purchases(shop_item_id);

-- Promotions to categories relationship
CREATE INDEX IF NOT EXISTS idx_shop_promotions_fk_category ON shop_promotions(applies_to_category_id);

-- Promotions to items relationship
CREATE INDEX IF NOT EXISTS idx_shop_promotions_fk_item ON shop_promotions(applies_to_item_id);