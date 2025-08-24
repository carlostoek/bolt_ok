-- Database migration script for PointTransaction implementation
-- This script adds the point_transactions table and removes redundant columns

-- Create the new point_transactions table
CREATE TABLE IF NOT EXISTS point_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    amount REAL NOT NULL,
    balance_after REAL NOT NULL,
    source VARCHAR(50) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_point_transactions_user_id ON point_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_point_transactions_created_at ON point_transactions(created_at);

-- Note: Removing columns from existing tables is handled by the application logic
-- The last_notified_points column in user_stats will be ignored by the ORM
-- The total_besitos_earned column in user_narrative_states will be ignored by the ORM