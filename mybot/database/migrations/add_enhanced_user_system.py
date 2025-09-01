"""
Database migration for Enhanced User System
Adds user_sessions, role_transitions tables and session_data column to users table.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from datetime import datetime

# revision identifiers
revision = 'enhanced_user_system_001'
down_revision = None  # Replace with actual previous revision
branch_labels = None
depends_on = None

def upgrade():
    """Apply enhanced user system changes."""
    
    # Add session_data column to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('session_data', sa.JSON(), nullable=True, default={}))
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('session_state', sa.String(), nullable=True, default='main_menu'),
        sa.Column('menu_position', sa.JSON(), nullable=True, default={}),
        sa.Column('preferences', sa.JSON(), nullable=True, default={}),
        sa.Column('last_interaction', sa.DateTime(), nullable=True, default=datetime.now),
        sa.Column('session_started', sa.DateTime(), nullable=True, default=datetime.now),
        sa.Column('character_consistency_score', sa.Float(), nullable=True, default=100.0),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.now),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=datetime.now),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create role_transitions table
    op.create_table('role_transitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('previous_role', sa.String(), nullable=True),
        sa.Column('new_role', sa.String(), nullable=False),
        sa.Column('transition_reason', sa.String(), nullable=True),
        sa.Column('transition_type', sa.String(), nullable=True, default='automatic'),
        sa.Column('performed_by', sa.BigInteger(), nullable=True),
        sa.Column('transition_metadata', sa.JSON(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.now),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for performance
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'], unique=False)
    op.create_index('idx_user_sessions_last_interaction', 'user_sessions', ['last_interaction'], unique=False)
    op.create_index('idx_role_transitions_user_id', 'role_transitions', ['user_id'], unique=False)
    op.create_index('idx_role_transitions_created_at', 'role_transitions', ['created_at'], unique=False)

def downgrade():
    """Revert enhanced user system changes."""
    
    # Drop indexes
    op.drop_index('idx_role_transitions_created_at', table_name='role_transitions')
    op.drop_index('idx_role_transitions_user_id', table_name='role_transitions')
    op.drop_index('idx_user_sessions_last_interaction', table_name='user_sessions')
    op.drop_index('idx_user_sessions_user_id', table_name='user_sessions')
    
    # Drop tables
    op.drop_table('role_transitions')
    op.drop_table('user_sessions')
    
    # Remove session_data column from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('session_data')

# Manual migration script for development/testing
if __name__ == "__main__":
    """
    Manual migration runner for development.
    Run this script directly to apply migrations.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine
    from database.base import Base
    import os
    
    async def run_migration():
        # Get database URL from environment or use default
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./diana_bot.db")
        
        engine = create_async_engine(database_url)
        
        try:
            async with engine.begin() as conn:
                print("Running enhanced user system migration...")
                
                # Create all tables (this will create new ones and skip existing)
                await conn.run_sync(Base.metadata.create_all)
                
                # Add session_data column if it doesn't exist
                try:
                    await conn.execute(sa.text(
                        "ALTER TABLE users ADD COLUMN session_data JSON DEFAULT '{}'"
                    ))
                    print("Added session_data column to users table")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"Note: session_data column addition: {e}")
                
                print("Migration completed successfully!")
                
        except Exception as e:
            print(f"Migration error: {e}")
            raise
        finally:
            await engine.dispose()
    
    asyncio.run(run_migration())