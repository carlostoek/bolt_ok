-- Migration: Add Master Storyline Support Tables
-- This migration adds all the necessary tables and columns for the enhanced master storyline system
-- Version: 2.2.0
-- Date: 2025-01-XX

-- =====================================================
-- 1. Enhance existing narrative_fragments_unified table
-- =====================================================

-- Add master storyline columns to narrative fragments
ALTER TABLE narrative_fragments_unified 
ADD COLUMN storyline_level INTEGER DEFAULT NULL,
ADD COLUMN tier_classification VARCHAR(20) DEFAULT NULL,
ADD COLUMN fragment_sequence INTEGER DEFAULT NULL,
ADD COLUMN requires_vip BOOLEAN DEFAULT FALSE,
ADD COLUMN vip_tier_required INTEGER DEFAULT 0,
ADD COLUMN mission_type VARCHAR(30) DEFAULT NULL,
ADD COLUMN validation_criteria JSON DEFAULT '{}',
ADD COLUMN archetyping_data JSON DEFAULT '{}',
ADD COLUMN diana_personality_weight INTEGER DEFAULT 95,
ADD COLUMN lucien_appearance_logic JSON DEFAULT '{}',
ADD COLUMN character_validation_required BOOLEAN DEFAULT TRUE,
ADD COLUMN avg_completion_time INTEGER DEFAULT 0,
ADD COLUMN user_satisfaction_score INTEGER DEFAULT 0;

-- Add indexes for performance
CREATE INDEX ix_narrative_fragments_unified_storyline ON narrative_fragments_unified(storyline_level);
CREATE INDEX ix_narrative_fragments_unified_tier ON narrative_fragments_unified(tier_classification);
CREATE INDEX ix_narrative_fragments_unified_sequence ON narrative_fragments_unified(fragment_sequence);
CREATE INDEX ix_narrative_fragments_unified_vip ON narrative_fragments_unified(requires_vip);

-- =====================================================
-- 2. Enhance existing user_narrative_states_unified table  
-- =====================================================

-- Add master storyline tracking columns
ALTER TABLE user_narrative_states_unified 
ADD COLUMN current_level INTEGER DEFAULT 1,
ADD COLUMN current_tier VARCHAR(20) DEFAULT 'los_kinkys',
ADD COLUMN tier_transition_history JSON DEFAULT '[]',
ADD COLUMN response_time_tracking JSON DEFAULT '[]',
ADD COLUMN interaction_patterns JSON DEFAULT '{}',
ADD COLUMN content_engagement_depth JSON DEFAULT '{}',
ADD COLUMN diana_interactions_validated INTEGER DEFAULT 0,
ADD COLUMN diana_consistency_average INTEGER DEFAULT 0,
ADD COLUMN character_validation_history JSON DEFAULT '[]',
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Add indexes
CREATE INDEX ix_user_narrative_states_unified_level ON user_narrative_states_unified(current_level);
CREATE INDEX ix_user_narrative_states_unified_tier ON user_narrative_states_unified(current_tier);

-- =====================================================
-- 3. Create new tables for master storyline system
-- =====================================================

-- User archetypes table
CREATE TABLE user_archetypes_unified (
    user_id BIGINT PRIMARY KEY,
    explorer_score INTEGER DEFAULT 0,
    direct_score INTEGER DEFAULT 0,
    romantic_score INTEGER DEFAULT 0,
    analytical_score INTEGER DEFAULT 0,
    persistent_score INTEGER DEFAULT 0,
    patient_score INTEGER DEFAULT 0,
    dominant_archetype VARCHAR(20) DEFAULT NULL,
    avg_response_time INTEGER DEFAULT 0,
    content_revisit_count INTEGER DEFAULT 0,
    deep_exploration_sessions INTEGER DEFAULT 0,
    question_engagement_rate INTEGER DEFAULT 0,
    emotional_vocabulary_usage INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_user_archetypes_unified_user ON user_archetypes_unified(user_id);
CREATE INDEX ix_user_archetypes_unified_dominant ON user_archetypes_unified(dominant_archetype);

-- User mission progress table
CREATE TABLE user_mission_progress_unified (
    user_id BIGINT PRIMARY KEY,
    current_level INTEGER DEFAULT 1,
    current_tier VARCHAR(20) DEFAULT 'los_kinkys',
    observation_missions_completed JSON DEFAULT '[]',
    comprehension_tests_passed JSON DEFAULT '[]',
    synthesis_challenges_completed JSON DEFAULT '[]',
    observation_accuracy INTEGER DEFAULT 0,
    comprehension_depth_score INTEGER DEFAULT 0,
    synthesis_creativity_score INTEGER DEFAULT 0,
    los_kinkys_fragments_completed JSON DEFAULT '[]',
    el_divan_fragments_completed JSON DEFAULT '[]',
    elite_fragments_completed JSON DEFAULT '[]',
    personality_evaluation_results JSON DEFAULT '{}',
    emotional_maturity_score INTEGER DEFAULT 0,
    diana_comprehension_score INTEGER DEFAULT 0,
    vip_access_granted BOOLEAN DEFAULT FALSE,
    vip_tier_level INTEGER DEFAULT 0,
    personalized_content_unlocked JSON DEFAULT '[]',
    circle_intimo_access BOOLEAN DEFAULT FALSE,
    guardian_of_secrets_status BOOLEAN DEFAULT FALSE,
    narrative_synthesis_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    level_progression_history JSON DEFAULT '[]',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_user_mission_progress_unified_user ON user_mission_progress_unified(user_id);
CREATE INDEX ix_user_mission_progress_unified_level ON user_mission_progress_unified(current_level);
CREATE INDEX ix_user_mission_progress_unified_tier ON user_mission_progress_unified(current_tier);

-- Character validation table
CREATE TABLE narrative_character_validation_unified (
    id VARCHAR(36) PRIMARY KEY,
    fragment_id VARCHAR(36) DEFAULT NULL,
    user_id BIGINT DEFAULT NULL,
    validated_content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    consistency_score INTEGER NOT NULL,
    mysterious_score INTEGER NOT NULL,
    seductive_score INTEGER NOT NULL,
    emotional_complexity_score INTEGER NOT NULL,
    intellectual_engagement_score INTEGER NOT NULL,
    meets_threshold BOOLEAN NOT NULL,
    violations_detected JSON DEFAULT '[]',
    recommendations JSON DEFAULT '[]',
    validation_context JSON DEFAULT '{}',
    archetype_influence VARCHAR(20) DEFAULT NULL,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fragment_id) REFERENCES narrative_fragments_unified(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_narrative_character_validation_unified_fragment ON narrative_character_validation_unified(fragment_id);
CREATE INDEX ix_narrative_character_validation_unified_score ON narrative_character_validation_unified(consistency_score);
CREATE INDEX ix_narrative_character_validation_unified_meets ON narrative_character_validation_unified(meets_threshold);

-- Lucien coordination table
CREATE TABLE lucien_coordination_unified (
    id VARCHAR(36) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    coordination_mode VARCHAR(30) NOT NULL,
    current_role VARCHAR(50) NOT NULL,
    trigger_conditions JSON DEFAULT '{}',
    appearance_context VARCHAR(100) DEFAULT NULL,
    planned_disappearance_at TIMESTAMP DEFAULT NULL,
    user_emotional_state VARCHAR(30) DEFAULT NULL,
    last_interaction_type VARCHAR(50) DEFAULT NULL,
    requires_coordination BOOLEAN DEFAULT FALSE,
    current_fragment_context VARCHAR(36) DEFAULT NULL,
    narrative_phase VARCHAR(30) NOT NULL,
    diana_availability BOOLEAN DEFAULT TRUE,
    appearance_history JSON DEFAULT '[]',
    coordination_effectiveness INTEGER DEFAULT 50,
    activated_at TIMESTAMP DEFAULT NULL,
    last_coordination_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_lucien_coordination_unified_user ON lucien_coordination_unified(user_id);
CREATE INDEX ix_lucien_coordination_unified_active ON lucien_coordination_unified(is_active);

-- =====================================================
-- 4. Create master storyline seed data
-- =====================================================

-- Insert sample master storyline fragments (would be populated with actual content)
-- This is just the structure - actual content would come from the narrative designer

INSERT INTO narrative_fragments_unified (
    id, title, content, fragment_type, storyline_level, tier_classification, 
    fragment_sequence, requires_vip, vip_tier_required, mission_type,
    diana_personality_weight, character_validation_required
) VALUES 
-- Los Kinkys tier (Free) - Levels 1-3
('ms_level_1_fragment_1', 'Bienvenida de Diana', 'Bienvenido a Los Kinkys...', 'STORY', 1, 'los_kinkys', 1, FALSE, 0, NULL, 95, TRUE),
('ms_level_1_fragment_2', 'Lucien y el Primer Desafío', 'Ah, otro visitante de Diana...', 'STORY', 1, 'los_kinkys', 2, FALSE, 0, 'observation', 95, TRUE),
('ms_level_2_fragment_1', 'El Regreso Observado', 'Volviste. Interesante...', 'STORY', 2, 'los_kinkys', 3, FALSE, 0, 'comprehension', 95, TRUE),

-- El Diván tier (VIP) - Levels 4-5
('ms_level_4_fragment_1', 'Bienvenida Íntima de Diana', 'Oh... finalmente decidiste cruzar...', 'STORY', 4, 'el_divan', 9, TRUE, 1, 'comprehension', 98, TRUE),
('ms_level_5_fragment_1', 'Diana Reconoce la Evolución', 'Mira cómo has crecido...', 'STORY', 5, 'el_divan', 11, TRUE, 1, 'synthesis', 98, TRUE),

-- Elite tier (Premium VIP) - Level 6
('ms_level_6_fragment_1', 'Diana Revela el Secreto Final', 'Hemos llegado al final del viaje...', 'STORY', 6, 'elite', 15, TRUE, 2, 'synthesis', 98, TRUE);

-- =====================================================
-- 5. Update existing data for compatibility
-- =====================================================

-- Set default values for existing fragments
UPDATE narrative_fragments_unified 
SET 
    storyline_level = 1,
    tier_classification = 'los_kinkys',
    diana_personality_weight = 95,
    character_validation_required = TRUE
WHERE storyline_level IS NULL;

-- Set default values for existing user states  
UPDATE user_narrative_states_unified 
SET 
    current_level = 1,
    current_tier = 'los_kinkys'
WHERE current_level IS NULL;

-- =====================================================
-- 6. Add constraints and validation
-- =====================================================

-- Add check constraints
ALTER TABLE narrative_fragments_unified 
ADD CONSTRAINT chk_storyline_level CHECK (storyline_level >= 1 AND storyline_level <= 6),
ADD CONSTRAINT chk_tier_classification CHECK (tier_classification IN ('los_kinkys', 'el_divan', 'elite')),
ADD CONSTRAINT chk_vip_tier_required CHECK (vip_tier_required >= 0 AND vip_tier_required <= 2),
ADD CONSTRAINT chk_diana_personality_weight CHECK (diana_personality_weight >= 0 AND diana_personality_weight <= 100);

ALTER TABLE user_narrative_states_unified 
ADD CONSTRAINT chk_current_level CHECK (current_level >= 1 AND current_level <= 6),
ADD CONSTRAINT chk_current_tier CHECK (current_tier IN ('los_kinkys', 'el_divan', 'elite'));

ALTER TABLE user_mission_progress_unified 
ADD CONSTRAINT chk_mission_current_level CHECK (current_level >= 1 AND current_level <= 6),
ADD CONSTRAINT chk_mission_current_tier CHECK (current_tier IN ('los_kinkys', 'el_divan', 'elite')),
ADD CONSTRAINT chk_vip_tier_level CHECK (vip_tier_level >= 0 AND vip_tier_level <= 2);

ALTER TABLE narrative_character_validation_unified 
ADD CONSTRAINT chk_consistency_score CHECK (consistency_score >= 0 AND consistency_score <= 100),
ADD CONSTRAINT chk_trait_scores CHECK (
    mysterious_score >= 0 AND mysterious_score <= 100 AND
    seductive_score >= 0 AND seductive_score <= 100 AND
    emotional_complexity_score >= 0 AND emotional_complexity_score <= 100 AND
    intellectual_engagement_score >= 0 AND intellectual_engagement_score <= 100
);

-- =====================================================
-- 7. Performance optimizations
-- =====================================================

-- Additional composite indexes for complex queries
CREATE INDEX ix_fragments_storyline_tier ON narrative_fragments_unified(storyline_level, tier_classification);
CREATE INDEX ix_fragments_vip_access ON narrative_fragments_unified(requires_vip, vip_tier_required);
CREATE INDEX ix_user_progress_level_tier ON user_mission_progress_unified(current_level, current_tier);
CREATE INDEX ix_validation_score_threshold ON narrative_character_validation_unified(consistency_score, meets_threshold);

-- =====================================================
-- 8. Triggers for automatic updates
-- =====================================================

-- Trigger to update user_narrative_states_unified.updated_at
DELIMITER //
CREATE TRIGGER update_user_narrative_states_unified_timestamp
    BEFORE UPDATE ON user_narrative_states_unified
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//
DELIMITER ;

-- Trigger to update user_archetypes_unified.updated_at
DELIMITER //
CREATE TRIGGER update_user_archetypes_unified_timestamp
    BEFORE UPDATE ON user_archetypes_unified
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//
DELIMITER ;

-- Trigger to update user_mission_progress_unified.updated_at
DELIMITER //
CREATE TRIGGER update_user_mission_progress_unified_timestamp
    BEFORE UPDATE ON user_mission_progress_unified
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//
DELIMITER ;

-- Trigger to update lucien_coordination_unified.updated_at
DELIMITER //
CREATE TRIGGER update_lucien_coordination_unified_timestamp
    BEFORE UPDATE ON lucien_coordination_unified
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//
DELIMITER ;

-- =====================================================
-- Migration Complete
-- =====================================================

-- Insert migration record
INSERT INTO migration_history (
    version, 
    description, 
    applied_at
) VALUES (
    '2.2.0',
    'Add Master Storyline Support Tables - Enhanced narrative system with archetyping, mission validation, VIP tiers, character consistency, and Lucien coordination',
    CURRENT_TIMESTAMP
);

-- Verify migration success
SELECT 
    'Migration completed successfully' as status,
    COUNT(*) as new_fragments_count
FROM narrative_fragments_unified 
WHERE storyline_level IS NOT NULL;