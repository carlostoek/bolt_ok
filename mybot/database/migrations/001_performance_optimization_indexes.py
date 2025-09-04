"""Performance optimization indexes migration.

This migration adds critical performance indexes for:
- User narrative progress queries (most frequent)
- Mission progress aggregation
- Character validation queries
- Multi-tenant isolation

Revision ID: 001_performance_optimization_indexes
Revises: 
Create Date: 2025-09-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Index

# revision identifiers, used by Alembic
revision = '001_performance_optimization_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add performance optimization indexes."""
    
    # Critical narrative progress query optimization
    # Query: User narrative progress with fragment joins
    op.create_index(
        'ix_users_narrative_progress_lookup',
        'users', 
        ['id', 'is_admin', 'role']
    )
    
    # Narrative fragment active lookup optimization 
    op.create_index(
        'ix_narrative_fragments_active_type_lookup',
        'narrative_fragments_unified',
        ['is_active', 'fragment_type', 'requires_vip', 'tier_classification']
    )
    
    # User narrative state optimization for progress tracking
    op.create_index(
        'ix_user_narrative_states_progress_lookup', 
        'user_narrative_states_unified',
        ['user_id', 'current_level', 'current_tier']
    )
    
    # Mission progress aggregation optimization
    op.create_index(
        'ix_user_mission_entries_progress_lookup',
        'user_mission_entries',
        ['user_id', 'completed', 'mission_id']
    )
    
    # Mission active lookup optimization
    op.create_index(
        'ix_missions_active_type_lookup',
        'missions',
        ['is_active', 'type', 'requires_action']
    )
    
    # User mission progress unified optimization
    op.create_index(
        'ix_user_mission_progress_tier_level_lookup',
        'user_mission_progress_unified',
        ['user_id', 'current_tier', 'current_level', 'vip_access_granted']
    )
    
    # Character validation performance optimization
    op.create_index(
        'ix_character_validation_score_lookup',
        'narrative_character_validation_unified', 
        ['meets_threshold', 'consistency_score', 'validated_at']
    )
    
    # User decision log optimization for duplicate prevention
    op.create_index(
        'ix_user_decision_log_duplicate_check',
        'user_decision_log_unified',
        ['user_id', 'fragment_id', 'made_at']
    )
    
    # User archetype lookup optimization
    op.create_index(
        'ix_user_archetypes_dominant_lookup',
        'user_archetypes_unified',
        ['user_id', 'dominant_archetype', 'updated_at']
    )
    
    # Lucien coordination active state optimization
    op.create_index(
        'ix_lucien_coordination_active_lookup',
        'lucien_coordination_unified',
        ['user_id', 'is_active', 'coordination_mode', 'diana_availability']
    )
    
    # User session state optimization for Diana menu system
    op.create_index(
        'ix_user_sessions_state_lookup',
        'user_sessions',
        ['user_id', 'session_state', 'last_interaction']
    )
    
    # Multi-tenant user isolation optimization
    op.create_index(
        'ix_users_tenant_isolation',
        'users',
        ['id', 'created_at', 'updated_at']
    )
    
    # Points and gamification lookup optimization
    op.create_index(
        'ix_users_points_level_lookup',
        'users',
        ['points', 'level', 'role', 'vip_expires_at']
    )
    
    # User stats activity lookup optimization
    op.create_index(
        'ix_user_stats_activity_lookup',
        'user_stats',
        ['user_id', 'last_activity_at', 'last_reaction_at']
    )
    
    # Button reaction performance optimization
    op.create_index(
        'ix_button_reactions_user_message_lookup',
        'button_reactions',
        ['user_id', 'message_id', 'created_at']
    )
    
    # User achievements lookup optimization
    op.create_index(
        'ix_user_achievements_lookup',
        'user_achievements',
        ['user_id', 'achievement_id', 'unlocked_at']
    )
    
    # User badges lookup optimization
    op.create_index(
        'ix_user_badges_active_lookup',
        'user_badges',
        ['user_id', 'badge_id', 'awarded_at']
    )
    
    # Lore pieces content type optimization
    op.create_index(
        'ix_lore_pieces_active_category_lookup',
        'lore_pieces',
        ['is_active', 'content_type', 'category']
    )
    
    # User lore pieces unlock optimization
    op.create_index(
        'ix_user_lore_pieces_unlock_lookup',
        'user_lore_pieces',
        ['user_id', 'lore_piece_id', 'unlocked_at']
    )
    
    # Audit and logging optimization
    op.create_index(
        'ix_interaction_logs_user_type_lookup',
        'interaction_logs',
        ['user_id', 'interaction_type', 'timestamp']
    )
    
    # Role transitions audit optimization
    op.create_index(
        'ix_role_transitions_user_lookup',
        'role_transitions',
        ['user_id', 'transition_type', 'created_at']
    )


def downgrade():
    """Remove performance optimization indexes."""
    
    # Remove all created indexes in reverse order
    op.drop_index('ix_role_transitions_user_lookup', table_name='role_transitions')
    op.drop_index('ix_interaction_logs_user_type_lookup', table_name='interaction_logs')
    op.drop_index('ix_user_lore_pieces_unlock_lookup', table_name='user_lore_pieces')
    op.drop_index('ix_lore_pieces_active_category_lookup', table_name='lore_pieces')
    op.drop_index('ix_user_badges_active_lookup', table_name='user_badges')
    op.drop_index('ix_user_achievements_lookup', table_name='user_achievements')
    op.drop_index('ix_button_reactions_user_message_lookup', table_name='button_reactions')
    op.drop_index('ix_user_stats_activity_lookup', table_name='user_stats')
    op.drop_index('ix_users_points_level_lookup', table_name='users')
    op.drop_index('ix_users_tenant_isolation', table_name='users')
    op.drop_index('ix_user_sessions_state_lookup', table_name='user_sessions')
    op.drop_index('ix_lucien_coordination_active_lookup', table_name='lucien_coordination_unified')
    op.drop_index('ix_user_archetypes_dominant_lookup', table_name='user_archetypes_unified')
    op.drop_index('ix_user_decision_log_duplicate_check', table_name='user_decision_log_unified')
    op.drop_index('ix_character_validation_score_lookup', table_name='narrative_character_validation_unified')
    op.drop_index('ix_user_mission_progress_tier_level_lookup', table_name='user_mission_progress_unified')
    op.drop_index('ix_missions_active_type_lookup', table_name='missions')
    op.drop_index('ix_user_mission_entries_progress_lookup', table_name='user_mission_entries')
    op.drop_index('ix_user_narrative_states_progress_lookup', table_name='user_narrative_states_unified')
    op.drop_index('ix_narrative_fragments_active_type_lookup', table_name='narrative_fragments_unified')
    op.drop_index('ix_users_narrative_progress_lookup', table_name='users')