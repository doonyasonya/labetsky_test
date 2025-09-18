"""create images table

Revision ID: 001
Revises: 
Create Date: 2025-09-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('images',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('original_url', sa.String(), nullable=False),
    sa.Column('thumbnails', sa.JSON(), server_default='{}', nullable=True),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_images_created_at'), 'images', ['created_at'], unique=False)
    op.create_index(op.f('ix_images_status'), 'images', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_images_status'), table_name='images')
    op.drop_index(op.f('ix_images_created_at'), table_name='images')
    op.drop_table('images')
