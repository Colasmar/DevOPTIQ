"""Add justification column to softskills

Revision ID: 20230312_add_justification
Revises: f921f6857574  # <- Mets ici l'ID de la dernière migration existante
Create Date: 2025-03-11 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# IMPORTANT : change "f921f6857574" selon la dernière révision de ton projet
revision = '20230312_add_justification'
down_revision = 'f921f6857574'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('softskills', sa.Column('justification', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('softskills', 'justification')
