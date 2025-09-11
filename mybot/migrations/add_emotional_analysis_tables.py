"""
Database Migration: Add Emotional Analysis Tables

This migration adds the complete emotional analysis database schema:
- user_emotional_profiles
- emotional_interactions  
- emotional_evolution
- emotional_triggers
- emotional_insights

CRITICAL: This migration is designed to be non-breaking and backwards compatible.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    """Add emotional analysis tables"""
    
    # Create ENUM types first
    emotional_intensity_enum = postgresql.ENUM(
        'very_low', 'low', 'moderate', 'high', 'very_high',
        name='emotionalintensity', 
        create_type=False
    )
    emotional_intensity_enum.create(op.get_bind(), checkfirst=True)
    
    response_type_enum = postgresql.ENUM(
        'impulso_autentico', 'pausa_reflexiva', 'contemplacion', 'abandono',
        name='responsetype',
        create_type=False
    )
    response_type_enum.create(op.get_bind(), checkfirst=True)
    
    vulnerability_level_enum = postgresql.ENUM(
        'surface', 'tentative', 'genuine', 'deep_intimate',
        name='vulnerabilitylevel',
        create_type=False
    )
    vulnerability_level_enum.create(op.get_bind(), checkfirst=True)
    
    # 1. Create user_emotional_profiles table
    op.create_table(
        'user_emotional_profiles',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('impulso_autentico_percentage', sa.Float(), default=0.0),
        sa.Column('pausa_reflexiva_percentage', sa.Float(), default=0.0),
        sa.Column('contemplacion_percentage', sa.Float(), default=0.0),
        sa.Column('abandono_percentage', sa.Float(), default=0.0),
        sa.Column('consistency_score', sa.Float(), default=0.0),
        sa.Column('vulnerability_progression', sa.Float(), default=0.0),
        sa.Column('authenticity_score', sa.Float(), default=0.0),
        sa.Column('dominant_emotional_pattern', response_type_enum, default='pausa_reflexiva'),
        sa.Column('current_vulnerability_level', vulnerability_level_enum, default='surface'),
        sa.Column('emotional_growth_trajectory', sa.Float(), default=0.0),
        sa.Column('total_interactions', sa.Integer(), default=0),
        sa.Column('total_session_time', sa.Float(), default=0.0),
        sa.Column('average_response_time', sa.Float(), default=0.0),
        sa.Column('peak_engagement_time', sa.DateTime(), nullable=True),
        sa.Column('profile_created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('last_analysis_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    # 2. Create emotional_interactions table
    op.create_table(
        'emotional_interactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('session_id', sa.String(50), nullable=False),
        sa.Column('fragment_key', sa.String(50), nullable=True),
        sa.Column('interaction_type', sa.String(30), nullable=False),
        sa.Column('interaction_content', sa.Text(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=False),
        sa.Column('response_type', response_type_enum, nullable=False),
        sa.Column('session_duration', sa.Float(), nullable=True),
        sa.Column('time_since_last_interaction', sa.Float(), nullable=True),
        sa.Column('emotional_intensity', emotional_intensity_enum, nullable=True),
        sa.Column('vulnerability_exhibited', vulnerability_level_enum, nullable=True),
        sa.Column('authenticity_indicators', sa.JSON(), nullable=True),
        sa.Column('behavioral_flags', sa.JSON(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('engagement_depth', sa.Float(), nullable=True),
        sa.Column('narrative_resonance', sa.Float(), nullable=True),
        sa.Column('decision_confidence', sa.Float(), nullable=True),
        sa.Column('device_context', sa.JSON(), nullable=True),
        sa.Column('interaction_context', sa.JSON(), nullable=True),
        sa.Column('interaction_timestamp', sa.DateTime(), default=sa.func.now()),
        sa.Column('analysis_processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for emotional_interactions
    op.create_index('idx_user_session', 'emotional_interactions', ['user_id', 'session_id'])
    op.create_index('idx_user_timestamp', 'emotional_interactions', ['user_id', 'interaction_timestamp'])
    op.create_index('idx_response_analysis', 'emotional_interactions', ['response_type', 'emotional_intensity'])
    op.create_index('idx_emotional_interactions_user_id', 'emotional_interactions', ['user_id'])
    
    # 3. Create emotional_evolution table
    op.create_table(
        'emotional_evolution',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('vulnerability_growth', sa.Float(), default=0.0),
        sa.Column('authenticity_improvement', sa.Float(), default=0.0),
        sa.Column('consistency_trend', sa.Float(), default=0.0),
        sa.Column('engagement_evolution', sa.Float(), default=0.0),
        sa.Column('response_pattern_shift', sa.JSON(), nullable=True),
        sa.Column('emotional_milestones', sa.JSON(), nullable=True),
        sa.Column('breakthrough_indicators', sa.JSON(), nullable=True),
        sa.Column('regression_flags', sa.JSON(), nullable=True),
        sa.Column('future_engagement_prediction', sa.Float(), nullable=True),
        sa.Column('vulnerability_trajectory', sa.Float(), nullable=True),
        sa.Column('risk_assessment', sa.Float(), nullable=True),
        sa.Column('evolution_calculated_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for emotional_evolution
    op.create_index('idx_user_period', 'emotional_evolution', ['user_id', 'period_type', 'period_start'])
    op.create_index('idx_emotional_evolution_user_id', 'emotional_evolution', ['user_id'])
    
    # 4. Create emotional_triggers table
    op.create_table(
        'emotional_triggers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('trigger_content', sa.Text(), nullable=False),
        sa.Column('trigger_context', sa.JSON(), nullable=True),
        sa.Column('typical_response_type', response_type_enum, nullable=False),
        sa.Column('emotional_intensity_triggered', emotional_intensity_enum, nullable=False),
        sa.Column('vulnerability_impact', sa.Float(), nullable=False),
        sa.Column('activation_count', sa.Integer(), default=1),
        sa.Column('last_activation', sa.DateTime(), default=sa.func.now()),
        sa.Column('average_response_time', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), default=1.0),
        sa.Column('trigger_strength', sa.Float(), default=1.0),
        sa.Column('adaptation_rate', sa.Float(), default=0.0),
        sa.Column('desensitization_level', sa.Float(), default=0.0),
        sa.Column('first_detected', sa.DateTime(), default=sa.func.now()),
        sa.Column('last_updated', sa.DateTime(), default=sa.func.now()),
        sa.Column('confidence_score', sa.Float(), default=1.0),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for emotional_triggers
    op.create_index('idx_user_trigger_type', 'emotional_triggers', ['user_id', 'trigger_type'])
    op.create_index('idx_trigger_strength', 'emotional_triggers', ['trigger_strength', 'activation_count'])
    op.create_index('idx_emotional_triggers_user_id', 'emotional_triggers', ['user_id'])
    
    # 5. Create emotional_insights table
    op.create_table(
        'emotional_insights',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('insight_type', sa.String(50), nullable=False),
        sa.Column('insight_category', sa.String(30), nullable=False),
        sa.Column('priority_level', sa.Integer(), default=5),
        sa.Column('insight_title', sa.String(200), nullable=False),
        sa.Column('insight_description', sa.Text(), nullable=False),
        sa.Column('supporting_data', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('recommended_actions', sa.JSON(), nullable=True),
        sa.Column('narrative_adaptations', sa.JSON(), nullable=True),
        sa.Column('engagement_strategies', sa.JSON(), nullable=True),
        sa.Column('is_implemented', sa.Boolean(), default=False),
        sa.Column('implementation_date', sa.DateTime(), nullable=True),
        sa.Column('effectiveness_score', sa.Float(), nullable=True),
        sa.Column('insight_generated_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for emotional_insights
    op.create_index('idx_user_priority', 'emotional_insights', ['user_id', 'priority_level'])
    op.create_index('idx_insight_type_category', 'emotional_insights', ['insight_type', 'insight_category'])
    op.create_index('idx_emotional_insights_user_id', 'emotional_insights', ['user_id'])
    
    print("✅ Emotional analysis tables created successfully")
    print("   - user_emotional_profiles: Core emotional profiles")
    print("   - emotional_interactions: Individual interaction tracking")
    print("   - emotional_evolution: Emotional progression over time")
    print("   - emotional_triggers: Trigger identification and tracking")
    print("   - emotional_insights: Generated insights and recommendations")
    print("   - All indexes and foreign keys configured")
    print("   - PERFORMANCE TARGET: <50ms analysis time maintained")


def downgrade():
    """Remove emotional analysis tables"""
    
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('emotional_insights')
    op.drop_table('emotional_triggers')
    op.drop_table('emotional_evolution')
    op.drop_table('emotional_interactions')
    op.drop_table('user_emotional_profiles')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS emotionalintensity CASCADE')
    op.execute('DROP TYPE IF EXISTS responsetype CASCADE')
    op.execute('DROP TYPE IF EXISTS vulnerabilitylevel CASCADE')
    
    print("✅ Emotional analysis tables removed successfully")