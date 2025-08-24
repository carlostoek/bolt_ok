-- Database migration script for VipTransaction implementation
-- This script adds the vip_transactions table for complete VIP state auditing

-- Create the new vip_transactions table
CREATE TABLE IF NOT EXISTS vip_transactions (
    id INTEGER PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR,
    source VARCHAR,
    source_id INTEGER,
    duration_days INTEGER,
    expires_at DATETIME,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes VARCHAR,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_vip_transactions_user_id ON vip_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_vip_transactions_created_at ON vip_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_vip_transactions_is_active ON vip_transactions(is_active);
CREATE INDEX IF NOT EXISTS idx_vip_transactions_expires_at ON vip_transactions(expires_at);