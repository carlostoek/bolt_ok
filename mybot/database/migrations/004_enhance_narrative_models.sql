-- Migration for enhancing narrative models
-- This migration adds new fields to story_fragments, user_narrative_states, and lore_pieces tables.
-- It also creates the new fragment_analytics and user_journey_analytics tables.

-- Enhance story_fragments table
ALTER TABLE story_fragments ADD COLUMN content_type VARCHAR(50) DEFAULT 'text';
ALTER TABLE story_fragments ADD COLUMN emotional_tone VARCHAR(50);
ALTER TABLE story_fragments ADD COLUMN user_archetype_tags TEXT;
ALTER TABLE story_fragments ADD COLUMN analytics_metadata TEXT;
ALTER TABLE story_fragments ADD COLUMN content_warnings TEXT;
ALTER TABLE story_fragments ADD COLUMN localization_data TEXT;
ALTER TABLE story_fragments ADD COLUMN complex_unlock_conditions TEXT;
ALTER TABLE story_fragments ADD COLUMN prerequisite_fragments TEXT;
ALTER TABLE story_fragments ADD COLUMN unlock_analytics TEXT;

-- Enhance user_narrative_states table
ALTER TABLE user_narrative_states ADD COLUMN choice_patterns TEXT;
ALTER TABLE user_narrative_states ADD COLUMN emotional_journey TEXT;
ALTER TABLE user_narrative_states ADD COLUMN archetype_classification TEXT;
ALTER TABLE user_narrative_states ADD COLUMN relationship_progress TEXT;
ALTER TABLE user_narrative_states ADD COLUMN engagement_metrics TEXT;
ALTER TABLE user_narrative_states ADD COLUMN content_preferences TEXT;
ALTER TABLE user_narrative_states ADD COLUMN progression_predictions TEXT;

-- Enhance lore_pieces table
ALTER TABLE lore_pieces ADD COLUMN rich_content_data TEXT;
ALTER TABLE lore_pieces ADD COLUMN content_metadata TEXT;
ALTER TABLE lore_pieces ADD COLUMN unlock_condition_tree TEXT;
ALTER TABLE lore_pieces ADD COLUMN related_lore_pieces TEXT;
ALTER TABLE lore_pieces ADD COLUMN access_analytics TEXT;
ALTER TABLE lore_pieces ADD COLUMN engagement_metrics TEXT;
ALTER TABLE lore_pieces ADD COLUMN content_effectiveness TEXT;

-- Create fragment_analytics table
CREATE TABLE IF NOT EXISTS fragment_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fragment_id VARCHAR(50) NOT NULL,
    total_views INTEGER DEFAULT 0,
    completion_rate REAL DEFAULT 0.0,
    average_time_spent REAL DEFAULT 0.0,
    choice_distribution TEXT,
    user_feedback_scores TEXT,
    conversion_metrics TEXT,
    FOREIGN KEY (fragment_id) REFERENCES story_fragments(key) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fragment_analytics_fragment_id ON fragment_analytics(fragment_id);

-- Create user_journey_analytics table
CREATE TABLE IF NOT EXISTS user_journey_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    journey_start DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_fragments_viewed INTEGER DEFAULT 0,
    total_choices_made INTEGER DEFAULT 0,
    archetype_evolution TEXT,
    emotional_progression TEXT,
    purchase_correlation TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_user_journey_analytics_user_id ON user_journey_analytics(user_id);
