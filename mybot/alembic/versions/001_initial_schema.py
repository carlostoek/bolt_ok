"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-26 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create missions table
    op.create_table('missions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reward_points', sa.Integer(), nullable=True),
        sa.Column('reward_currency', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('completion_conditions', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_repeatable', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_missions_id'), 'missions', ['id'], unique=False)
    op.create_index(op.f('ix_missions_title'), 'missions', ['title'], unique=False)

    # Create badges table
    op.create_table('badges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_path', sa.String(length=500), nullable=True),
        sa.Column('rarity', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_badges_id'), 'badges', ['id'], unique=False)
    op.create_index(op.f('ix_badges_name'), 'badges', ['name'], unique=False)

    # Create achievements table
    op.create_table('achievements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('badge_id', sa.Integer(), nullable=True),
        sa.Column('trigger_condition', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_achievements_id'), 'achievements', ['id'], unique=False)
    op.create_index(op.f('ix_achievements_name'), 'achievements', ['name'], unique=False)

    # Create automation_triggers table
    op.create_table('automation_triggers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_type', sa.String(length=100), nullable=False),
        sa.Column('trigger_condition', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_triggers_id'), 'automation_triggers', ['id'], unique=False)
    op.create_index(op.f('ix_automation_triggers_name'), 'automation_triggers', ['name'], unique=False)

    # Create lore_pieces table
    op.create_table('lore_pieces',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lore_pieces_id'), 'lore_pieces', ['id'], unique=False)
    op.create_index(op.f('ix_lore_pieces_title'), 'lore_pieces', ['title'], unique=False)

    # Create shop_items table
    op.create_table('shop_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('stock_quantity', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shop_items_id'), 'shop_items', ['id'], unique=False)
    op.create_index(op.f('ix_shop_items_name'), 'shop_items', ['name'], unique=False)

    # Create story_fragments table
    op.create_table('story_fragments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('fragment_type', sa.String(length=50), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_story_fragments_id'), 'story_fragments', ['id'], unique=False)
    op.create_index(op.f('ix_story_fragments_title'), 'story_fragments', ['title'], unique=False)

    # Create inventory_items table
    op.create_table('inventory_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('shop_item_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('is_consumed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['shop_item_id'], ['shop_items.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_items_id'), 'inventory_items', ['id'], unique=False)

    # Create narrative_choices table
    op.create_table('narrative_choices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('source_fragment_id', sa.Integer(), nullable=True),
        sa.Column('target_fragment_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['source_fragment_id'], ['story_fragments.id'], ),
        sa.ForeignKeyConstraint(['target_fragment_id'], ['story_fragments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_narrative_choices_id'), 'narrative_choices', ['id'], unique=False)

    # Create product_files table
    op.create_table('product_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('shop_item_id', sa.Integer(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['shop_item_id'], ['shop_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_files_id'), 'product_files', ['id'], unique=False)

    # Create rewards table
    op.create_table('rewards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('mission_id', sa.Integer(), nullable=True),
        sa.Column('reward_type', sa.String(length=50), nullable=False),
        sa.Column('reward_value', sa.Integer(), nullable=True),
        sa.Column('reward_item_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rewards_id'), 'rewards', ['id'], unique=False)

    # Create trigger_actions table
    op.create_table('trigger_actions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trigger_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['trigger_id'], ['automation_triggers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trigger_actions_id'), 'trigger_actions', ['id'], unique=False)

    # Create user_fragment_views table
    op.create_table('user_fragment_views',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('fragment_id', sa.Integer(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['fragment_id'], ['story_fragments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_fragment_views_id'), 'user_fragment_views', ['id'], unique=False)

    # Create user_lore_pieces table
    op.create_table('user_lore_pieces',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('lore_piece_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lore_piece_id'], ['lore_pieces.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_lore_pieces_id'), 'user_lore_pieces', ['id'], unique=False)

    # Create user_mission_entries table
    op.create_table('user_mission_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('mission_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_mission_entries_id'), 'user_mission_entries', ['id'], unique=False)

    # Create user_narrative_states table
    op.create_table('user_narrative_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('current_fragment_id', sa.Integer(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['current_fragment_id'], ['story_fragments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_narrative_states_id'), 'user_narrative_states', ['id'], unique=False)

    # Create user_purchases table
    op.create_table('user_purchases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('shop_item_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['shop_item_id'], ['shop_items.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_purchases_id'), 'user_purchases', ['id'], unique=False)

    # Create trigger_execution_logs table
    op.create_table('trigger_execution_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=True),
        sa.Column('execution_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_successful', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['action_id'], ['trigger_actions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trigger_execution_logs_id'), 'trigger_execution_logs', ['id'], unique=False)

    # Create indexes for better query performance
    op.create_index('idx_users_active', 'users', ['is_active'])
    op.create_index('idx_missions_active', 'missions', ['is_active'])
    op.create_index('idx_story_fragments_published', 'story_fragments', ['is_published'])
    op.create_index('idx_lore_pieces_published', 'lore_pieces', ['is_published'])
    op.create_index('idx_shop_items_active', 'shop_items', ['is_active'])
    op.create_index('idx_inventory_items_user', 'inventory_items', ['user_id'])
    op.create_index('idx_inventory_items_item', 'inventory_items', ['shop_item_id'])
    op.create_index('idx_user_purchases_user', 'user_purchases', ['user_id'])
    op.create_index('idx_user_purchases_item', 'user_purchases', ['shop_item_id'])
    op.create_index('idx_user_mission_entries_user', 'user_mission_entries', ['user_id'])
    op.create_index('idx_user_mission_entries_mission', 'user_mission_entries', ['mission_id'])
    op.create_index('idx_user_mission_entries_completed', 'user_mission_entries', ['is_completed'])


def downgrade() -> None:
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_index(op.f('ix_trigger_execution_logs_id'), table_name='trigger_execution_logs')
    op.drop_table('trigger_execution_logs')
    
    op.drop_index(op.f('ix_user_purchases_id'), table_name='user_purchases')
    op.drop_index('idx_user_purchases_item', table_name='user_purchases')
    op.drop_index('idx_user_purchases_user', table_name='user_purchases')
    op.drop_table('user_purchases')
    
    op.drop_index(op.f('ix_user_narrative_states_id'), table_name='user_narrative_states')
    op.drop_table('user_narrative_states')
    
    op.drop_index(op.f('ix_user_mission_entries_id'), table_name='user_mission_entries')
    op.drop_index('idx_user_mission_entries_completed', table_name='user_mission_entries')
    op.drop_index('idx_user_mission_entries_mission', table_name='user_mission_entries')
    op.drop_index('idx_user_mission_entries_user', table_name='user_mission_entries')
    op.drop_table('user_mission_entries')
    
    op.drop_index(op.f('ix_user_lore_pieces_id'), table_name='user_lore_pieces')
    op.drop_table('user_lore_pieces')
    
    op.drop_index(op.f('ix_user_fragment_views_id'), table_name='user_fragment_views')
    op.drop_table('user_fragment_views')
    
    op.drop_index(op.f('ix_trigger_actions_id'), table_name='trigger_actions')
    op.drop_table('trigger_actions')
    
    op.drop_index(op.f('ix_rewards_id'), table_name='rewards')
    op.drop_table('rewards')
    
    op.drop_index(op.f('ix_product_files_id'), table_name='product_files')
    op.drop_table('product_files')
    
    op.drop_index(op.f('ix_narrative_choices_id'), table_name='narrative_choices')
    op.drop_table('narrative_choices')
    
    op.drop_index(op.f('ix_inventory_items_id'), table_name='inventory_items')
    op.drop_index('idx_inventory_items_item', table_name='inventory_items')
    op.drop_index('idx_inventory_items_user', table_name='inventory_items')
    op.drop_table('inventory_items')
    
    op.drop_index(op.f('ix_story_fragments_title'), table_name='story_fragments')
    op.drop_index(op.f('ix_story_fragments_id'), table_name='story_fragments')
    op.drop_index('idx_story_fragments_published', table_name='story_fragments')
    op.drop_table('story_fragments')
    
    op.drop_index(op.f('ix_shop_items_name'), table_name='shop_items')
    op.drop_index(op.f('ix_shop_items_id'), table_name='shop_items')
    op.drop_index('idx_shop_items_active', table_name='shop_items')
    op.drop_table('shop_items')
    
    op.drop_index(op.f('ix_lore_pieces_title'), table_name='lore_pieces')
    op.drop_index(op.f('ix_lore_pieces_id'), table_name='lore_pieces')
    op.drop_index('idx_lore_pieces_published', table_name='lore_pieces')
    op.drop_table('lore_pieces')
    
    op.drop_index(op.f('ix_automation_triggers_name'), table_name='automation_triggers')
    op.drop_index(op.f('ix_automation_triggers_id'), table_name='automation_triggers')
    op.drop_table('automation_triggers')
    
    op.drop_index(op.f('ix_achievements_name'), table_name='achievements')
    op.drop_index(op.f('ix_achievements_id'), table_name='achievements')
    op.drop_table('achievements')
    
    op.drop_index(op.f('ix_badges_name'), table_name='badges')
    op.drop_index(op.f('ix_badges_id'), table_name='badges')
    op.drop_table('badges')
    
    op.drop_index(op.f('ix_missions_title'), table_name='missions')
    op.drop_index(op.f('ix_missions_id'), table_name='missions')
    op.drop_index('idx_missions_active', table_name='missions')
    op.drop_table('missions')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index('idx_users_active', table_name='users')
    op.drop_table('users')