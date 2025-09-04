#!/usr/bin/env python3
"""
Script to create missing unified narrative database tables.
This script creates the user_mission_progress_unified and user_archetypes_unified tables
that are required for the MVP narrative system.
"""

import asyncio
import sqlite3
from pathlib import Path

def create_missing_tables_sync():
    """Create missing tables using synchronous SQLite operations."""
    
    # Find the database file
    db_files = ['telegram_bot.db', 'diana_bot.db', 'bot.db']
    db_path = None
    
    for db_file in db_files:
        if Path(db_file).exists():
            db_path = db_file
            break
    
    if not db_path:
        print("❌ No database file found. Checked for:", db_files)
        return False
    
    print(f"📁 Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Existing tables: {len(existing_tables)} found")
        
        # Create user_mission_progress_unified table
        create_mission_progress_table = """
        CREATE TABLE IF NOT EXISTS user_mission_progress_unified (
            user_id BIGINT PRIMARY KEY,
            current_level INTEGER DEFAULT 1 NOT NULL,
            current_tier VARCHAR(20) DEFAULT 'los_kinkys' NOT NULL,
            observation_missions_completed JSON DEFAULT '[]' NOT NULL,
            comprehension_tests_passed JSON DEFAULT '[]' NOT NULL,
            synthesis_challenges_completed JSON DEFAULT '[]' NOT NULL,
            observation_accuracy INTEGER DEFAULT 0 NOT NULL,
            comprehension_depth_score INTEGER DEFAULT 0 NOT NULL,
            synthesis_creativity_score INTEGER DEFAULT 0 NOT NULL,
            los_kinkys_fragments_completed JSON DEFAULT '[]' NOT NULL,
            el_divan_fragments_completed JSON DEFAULT '[]' NOT NULL,
            elite_fragments_completed JSON DEFAULT '[]' NOT NULL,
            personality_evaluation_results JSON DEFAULT '{}' NOT NULL,
            emotional_maturity_score INTEGER DEFAULT 0 NOT NULL,
            diana_comprehension_score INTEGER DEFAULT 0 NOT NULL,
            vip_access_granted BOOLEAN DEFAULT 0 NOT NULL,
            vip_tier_level INTEGER DEFAULT 0 NOT NULL,
            personalized_content_unlocked JSON DEFAULT '[]' NOT NULL,
            circle_intimo_access BOOLEAN DEFAULT 0 NOT NULL,
            guardian_of_secrets_status BOOLEAN DEFAULT 0 NOT NULL,
            narrative_synthesis_completed BOOLEAN DEFAULT 0 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            level_progression_history JSON DEFAULT '[]' NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        cursor.execute(create_mission_progress_table)
        print("✅ Created/verified user_mission_progress_unified table")
        
        # Create user_archetypes_unified table
        create_archetypes_table = """
        CREATE TABLE IF NOT EXISTS user_archetypes_unified (
            user_id BIGINT PRIMARY KEY,
            explorer_score INTEGER DEFAULT 0 NOT NULL,
            direct_score INTEGER DEFAULT 0 NOT NULL,
            romantic_score INTEGER DEFAULT 0 NOT NULL,
            analytical_score INTEGER DEFAULT 0 NOT NULL,
            persistent_score INTEGER DEFAULT 0 NOT NULL,
            patient_score INTEGER DEFAULT 0 NOT NULL,
            dominant_archetype VARCHAR(20),
            avg_response_time INTEGER DEFAULT 0 NOT NULL,
            content_revisit_count INTEGER DEFAULT 0 NOT NULL,
            deep_exploration_sessions INTEGER DEFAULT 0 NOT NULL,
            question_engagement_rate INTEGER DEFAULT 0 NOT NULL,
            emotional_vocabulary_usage INTEGER DEFAULT 0 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        cursor.execute(create_archetypes_table)
        print("✅ Created/verified user_archetypes_unified table")
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_mission_progress_unified_user ON user_mission_progress_unified (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_mission_progress_unified_level ON user_mission_progress_unified (current_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_mission_progress_unified_tier ON user_mission_progress_unified (current_tier)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_archetypes_unified_user ON user_archetypes_unified (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_archetypes_unified_dominant ON user_archetypes_unified (dominant_archetype)")
        
        print("✅ Created performance indexes")
        
        # Create user_decision_log_unified table
        create_decision_log_table = """
        CREATE TABLE IF NOT EXISTS user_decision_log_unified (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            fragment_id VARCHAR(255) NOT NULL,
            decision_choice VARCHAR(100) NOT NULL,
            points_awarded INTEGER DEFAULT 0 NOT NULL,
            clues_unlocked JSON DEFAULT '[]' NOT NULL,
            made_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (fragment_id) REFERENCES narrative_fragments_unified (id) ON DELETE CASCADE
        )
        """
        
        cursor.execute(create_decision_log_table)
        print("✅ Created/verified user_decision_log_unified table")
        
        # Create indexes for user_decision_log_unified
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_decision_log_unified_user ON user_decision_log_unified (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_decision_log_unified_time ON user_decision_log_unified (made_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_decision_log_unified_fragment ON user_decision_log_unified (fragment_id)")
        
        # Create user_narrative_states_unified table
        create_narrative_states_table = """
        CREATE TABLE IF NOT EXISTS user_narrative_states_unified (
            user_id BIGINT PRIMARY KEY,
            current_fragment_id VARCHAR(255),
            visited_fragments JSON DEFAULT '[]' NOT NULL,
            completed_fragments JSON DEFAULT '[]' NOT NULL,
            unlocked_clues JSON DEFAULT '[]' NOT NULL,
            current_level INTEGER DEFAULT 1 NOT NULL,
            current_tier VARCHAR(20) DEFAULT 'los_kinkys' NOT NULL,
            tier_transition_history JSON DEFAULT '[]' NOT NULL,
            response_time_tracking JSON DEFAULT '[]' NOT NULL,
            interaction_patterns JSON DEFAULT '{}' NOT NULL,
            content_engagement_depth JSON DEFAULT '{}' NOT NULL,
            diana_interactions_validated INTEGER DEFAULT 0 NOT NULL,
            diana_consistency_average INTEGER DEFAULT 0 NOT NULL,
            character_validation_history JSON DEFAULT '[]' NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        cursor.execute(create_narrative_states_table)
        print("✅ Created/verified user_narrative_states_unified table")
        
        # Create narrative_fragments_unified table
        create_narrative_fragments_table = """
        CREATE TABLE IF NOT EXISTS narrative_fragments_unified (
            id VARCHAR(255) PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            fragment_type VARCHAR(20) NOT NULL,
            choices JSON DEFAULT '[]' NOT NULL,
            triggers JSON DEFAULT '{}' NOT NULL,
            required_clues JSON DEFAULT '[]' NOT NULL,
            storyline_level INTEGER,
            tier_classification VARCHAR(20),
            fragment_sequence INTEGER,
            requires_vip BOOLEAN DEFAULT 0 NOT NULL,
            vip_tier_required INTEGER DEFAULT 0 NOT NULL,
            mission_type VARCHAR(30),
            validation_criteria JSON DEFAULT '{}' NOT NULL,
            archetyping_data JSON DEFAULT '{}' NOT NULL,
            diana_personality_weight INTEGER DEFAULT 95 NOT NULL,
            lucien_appearance_logic JSON DEFAULT '{}' NOT NULL,
            character_validation_required BOOLEAN DEFAULT 1 NOT NULL,
            avg_completion_time INTEGER DEFAULT 0 NOT NULL,
            user_satisfaction_score INTEGER DEFAULT 0 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1 NOT NULL
        )
        """
        
        cursor.execute(create_narrative_fragments_table)
        print("✅ Created/verified narrative_fragments_unified table")
        
        # Create indexes for narrative fragments
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_narrative_fragments_unified_type_active ON narrative_fragments_unified (fragment_type, is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_narrative_fragments_unified_active ON narrative_fragments_unified (is_active)")
        
        # Commit all changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%unified%' ORDER BY name")
        unified_tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Unified tables now present: {unified_tables}")
        
        # Test basic queries
        test_tables = [
            'user_mission_progress_unified',
            'user_archetypes_unified',
            'user_decision_log_unified',
            'user_narrative_states_unified',
            'narrative_fragments_unified'
        ]
        
        for table in test_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Table {table}: {count} records")
            except Exception as e:
                print(f"❌ Table {table} error: {e}")
        
        conn.close()
        print("\n🎉 Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    success = create_missing_tables_sync()
    if success:
        print("\n✅ All missing tables created successfully!")
    else:
        print("\n❌ Failed to create some or all tables.")