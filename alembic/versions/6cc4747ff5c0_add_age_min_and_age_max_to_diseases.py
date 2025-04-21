"""add age_min and age_max to diseases

Revision ID: 6cc4747ff5c0
Revises: 782bb4a05d1c
Create Date: 2025-04-20 00:37:53.401513
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6cc4747ff5c0'
down_revision: Union[str, None] = '782bb4a05d1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('diseases', sa.Column('age_min', sa.Integer(), nullable=True))
    op.add_column('diseases', sa.Column('age_max', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('diseases', 'age_max')
    op.drop_column('diseases', 'age_min')