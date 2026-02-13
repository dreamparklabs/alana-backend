"""Add sso_subject_id to users table

Revision ID: 002
Revises: 001_initial
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('sso_subject_id', sa.String(255), nullable=True))
    op.create_index('ix_users_sso_subject_id', 'users', ['sso_subject_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_sso_subject_id', table_name='users')
    op.drop_column('users', 'sso_subject_id')
