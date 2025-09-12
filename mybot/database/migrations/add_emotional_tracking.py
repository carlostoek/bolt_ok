# database/migrations/add_emotional_tracking.py
"""
Database Migration: Add Emotional Tracking Tables
Surgical extension that adds emotional intelligence without modifying existing schema.
All new tables reference existing User.id as foreign key.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class EmotionalTrackingMigration:
    """
    Handles creation of emotional tracking tables.
    Safe to run multiple times - checks for existing tables.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def run_migration(self) -> bool:
        """
        Executes the complete emotional tracking migration.
        Returns True if successful, False if any errors.
        """
        try:
            logger.info("Starting emotional tracking database migration...")
            
            # Create all emotional tracking tables
            await self._create_emotional_enums()
            await self._create_user_emotional_profiles_table()
            await self._create_emotional_interactions_table()
            await self._create_conversation_memories_table()
            await self._create_emotional_triggers_table()
            await self._create_emotional_analysis_sessions_table()
            
            # Add indexes for performance
            await self._create_indexes()
            
            await self.session.commit()
            logger.info("Emotional tracking migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await self.session.rollback()
            return False
    
    async def _create_emotional_enums(self):
        """Create enum types for emotional tracking"""
        
        # Archetype classification enum
        archetype_enum = """
        DO $$ BEGIN
            CREATE TYPE archetype_classification AS ENUM (
                'explorer', 'achiever', 'socializer', 'creator', 
                'protector', 'challenger', 'undefined'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
        
        # Emotional state enum
        emotional_state_enum = """
        DO $$ BEGIN
            CREATE TYPE emotional_state AS ENUM (
                'curious', 'excited', 'contemplative', 'playful', 'serious',
                'nostalgic', 'anxious', 'confident', 'vulnerable', 'neutral'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
        
        # Interaction type enum
        interaction_type_enum = """
        DO $$ BEGIN
            CREATE TYPE interaction_type AS ENUM (
                'message_response', 'choice_selection', 'reaction_pattern',
                'narrative_engagement', 'achievement_response', 
                'vulnerability_moment', 'authenticity_display'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
        
        await self.session.execute(text(archetype_enum))
        await self.session.execute(text(emotional_state_enum))
        await self.session.execute(text(interaction_type_enum))
        
        logger.info("Created emotional tracking enums")
    
    async def _create_user_emotional_profiles_table(self):
        """Create user emotional profiles table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS user_emotional_profiles (
            user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            archetype_classification archetype_classification DEFAULT 'undefined' NOT NULL,
            archetype_confidence REAL DEFAULT 0.0,
            emotional_signature JSONB DEFAULT '{}',
            dominant_emotion emotional_state DEFAULT 'neutral',
            emotional_consistency REAL DEFAULT 0.5,
            vulnerability_level REAL DEFAULT 0.0,
            authenticity_score REAL DEFAULT 0.5,
            openness_factor REAL DEFAULT 0.5,
            response_time_pattern JSONB DEFAULT '{}',
            engagement_depth REAL DEFAULT 0.0,
            narrative_preference VARCHAR,
            profile_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_emotion_detected_at TIMESTAMP,
            total_interactions_analyzed INTEGER DEFAULT 0,
            classification_version VARCHAR DEFAULT '1.0'
        );
        """
        
        await self.session.execute(text(sql))
        logger.info("Created user_emotional_profiles table")
    
    async def _create_emotional_interactions_table(self):
        """Create emotional interactions tracking table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS emotional_interactions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            interaction_type interaction_type NOT NULL,
            emotional_context emotional_state,
            response_timing REAL,
            response_length INTEGER DEFAULT 0,
            response_complexity REAL DEFAULT 0.0,
            vulnerability_displayed REAL DEFAULT 0.0,
            authenticity_score REAL DEFAULT 0.5,
            emotional_intensity REAL DEFAULT 0.5,
            narrative_context VARCHAR,
            previous_emotion emotional_state,
            trigger_keywords JSONB DEFAULT '[]',
            interaction_metadata JSONB DEFAULT '{}',
            interaction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        await self.session.execute(text(sql))
        logger.info("Created emotional_interactions table")
    
    async def _create_conversation_memories_table(self):
        """Create conversation memories table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS conversation_memories (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            conversation_point VARCHAR NOT NULL,
            memory_type VARCHAR DEFAULT 'emotional',
            emotional_state emotional_state NOT NULL,
            memory_reference TEXT,
            emotional_impact REAL DEFAULT 0.5,
            user_reaction TEXT,
            narrative_fragment_key VARCHAR,
            choice_made VARCHAR,
            emotional_trigger VARCHAR,
            related_memory_ids JSONB DEFAULT '[]',
            memory_cluster VARCHAR,
            memory_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            memory_strength REAL DEFAULT 1.0,
            last_referenced_at TIMESTAMP,
            is_core_memory BOOLEAN DEFAULT FALSE,
            affects_future_narrative BOOLEAN DEFAULT TRUE,
            requires_sensitivity BOOLEAN DEFAULT FALSE
        );
        """
        
        await self.session.execute(text(sql))
        logger.info("Created conversation_memories table")
    
    async def _create_emotional_triggers_table(self):
        """Create emotional triggers table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS emotional_triggers (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            trigger_keyword VARCHAR NOT NULL,
            trigger_context VARCHAR,
            emotional_response emotional_state NOT NULL,
            trigger_strength REAL DEFAULT 0.5,
            confidence_level REAL DEFAULT 0.5,
            frequency_encountered INTEGER DEFAULT 1,
            typical_response_time REAL,
            associated_emotions JSONB DEFAULT '[]',
            narrative_impact VARCHAR,
            first_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_positive_trigger BOOLEAN,
            requires_careful_handling BOOLEAN DEFAULT FALSE,
            can_be_used_narratively BOOLEAN DEFAULT TRUE
        );
        """
        
        await self.session.execute(text(sql))
        logger.info("Created emotional_triggers table")
    
    async def _create_emotional_analysis_sessions_table(self):
        """Create emotional analysis sessions table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS emotional_analysis_sessions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            analysis_type VARCHAR NOT NULL,
            model_version VARCHAR DEFAULT '1.0',
            session_duration REAL,
            emotions_detected JSONB DEFAULT '[]',
            confidence_scores JSONB DEFAULT '{}',
            archetype_adjustments JSONB DEFAULT '{}',
            interactions_processed INTEGER DEFAULT 0,
            accuracy_score REAL,
            false_positive_rate REAL,
            session_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_completed_at TIMESTAMP,
            manual_review_required BOOLEAN DEFAULT FALSE,
            analysis_quality_score REAL
        );
        """
        
        await self.session.execute(text(sql))
        logger.info("Created emotional_analysis_sessions table")
    
    async def _create_indexes(self):
        """Create performance indexes on emotional tracking tables"""
        
        indexes = [
            # User-based lookups
            "CREATE INDEX IF NOT EXISTS idx_emotional_interactions_user_id ON emotional_interactions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_memories_user_id ON conversation_memories(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_emotional_triggers_user_id ON emotional_triggers(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_emotional_analysis_sessions_user_id ON emotional_analysis_sessions(user_id)",
            
            # Time-based queries
            "CREATE INDEX IF NOT EXISTS idx_emotional_interactions_timestamp ON emotional_interactions(interaction_timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_memories_created ON conversation_memories(memory_created_at DESC)",
            
            # Emotional state analysis
            "CREATE INDEX IF NOT EXISTS idx_emotional_interactions_state ON emotional_interactions(emotional_context)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_memories_state ON conversation_memories(emotional_state)",
            
            # Core memories lookup
            "CREATE INDEX IF NOT EXISTS idx_conversation_memories_core ON conversation_memories(user_id, is_core_memory, emotional_impact DESC)",
            
            # Trigger keyword lookup
            "CREATE INDEX IF NOT EXISTS idx_emotional_triggers_keyword ON emotional_triggers(trigger_keyword)",
            
            # Analysis performance
            "CREATE INDEX IF NOT EXISTS idx_emotional_interactions_user_time ON emotional_interactions(user_id, interaction_timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_memories_user_impact ON conversation_memories(user_id, emotional_impact DESC)"
        ]
        
        for index_sql in indexes:
            await self.session.execute(text(index_sql))
        
        logger.info("Created performance indexes for emotional tracking tables")
    
    async def verify_migration(self) -> Dict[str, bool]:
        """
        Verifies that all emotional tracking tables were created successfully.
        Returns dict with table names and their existence status.
        """
        tables_to_check = [
            'user_emotional_profiles',
            'emotional_interactions', 
            'conversation_memories',
            'emotional_triggers',
            'emotional_analysis_sessions'
        ]
        
        verification_results = {}
        
        for table_name in tables_to_check:
            try:
                result = await self.session.execute(
                    text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
                )
                exists = result.scalar()
                verification_results[table_name] = exists
                
            except Exception as e:
                logger.error(f"Error checking table {table_name}: {e}")
                verification_results[table_name] = False
        
        return verification_results
    
    async def rollback_migration(self) -> bool:
        """
        CAUTION: Completely removes all emotional tracking tables and data.
        Only use during development or if migration needs to be completely undone.
        """
        try:
            logger.warning("ROLLING BACK emotional tracking migration - ALL DATA WILL BE LOST")
            
            # Drop tables in reverse dependency order
            drop_statements = [
                "DROP TABLE IF EXISTS emotional_analysis_sessions CASCADE",
                "DROP TABLE IF EXISTS emotional_triggers CASCADE", 
                "DROP TABLE IF EXISTS conversation_memories CASCADE",
                "DROP TABLE IF EXISTS emotional_interactions CASCADE",
                "DROP TABLE IF EXISTS user_emotional_profiles CASCADE",
                "DROP TYPE IF EXISTS interaction_type CASCADE",
                "DROP TYPE IF EXISTS emotional_state CASCADE", 
                "DROP TYPE IF EXISTS archetype_classification CASCADE"
            ]
            
            for statement in drop_statements:
                await self.session.execute(text(statement))
            
            await self.session.commit()
            logger.info("Emotional tracking migration rolled back successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            await self.session.rollback()
            return False


async def run_emotional_tracking_migration(session: AsyncSession) -> bool:
    """
    Convenience function to run the emotional tracking migration.
    Can be called from existing database setup scripts.
    """
    migration = EmotionalTrackingMigration(session)
    return await migration.run_migration()


async def verify_emotional_tracking_migration(session: AsyncSession) -> Dict[str, bool]:
    """
    Convenience function to verify the emotional tracking migration.
    """
    migration = EmotionalTrackingMigration(session)
    return await migration.verify_migration()