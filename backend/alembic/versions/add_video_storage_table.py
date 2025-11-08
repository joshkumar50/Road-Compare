"""Add video storage table for database storage

Revision ID: add_video_storage_001
Revises: 
Create Date: 2024-11-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_video_storage_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create video_storage table for database video storage
    op.create_table('video_storage',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=True),
        sa.Column('filename', sa.String(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('size', sa.String(), nullable=True),
        sa.Column('data', sa.LargeBinary(), nullable=True),
        sa.Column('data_url', sa.Text(), nullable=True),
        sa.Column('video_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_storage_key'), 'video_storage', ['key'], unique=True)
    
    # Add index for faster queries
    op.create_index('ix_video_storage_created_at', 'video_storage', ['created_at'])


def downgrade():
    op.drop_index('ix_video_storage_created_at', table_name='video_storage')
    op.drop_index(op.f('ix_video_storage_key'), table_name='video_storage')
    op.drop_table('video_storage')
