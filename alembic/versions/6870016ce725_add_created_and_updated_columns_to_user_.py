"""Add created and updated columns to user_diseases

Revision ID: 6870016ce725
Revises: 7d6562db3339
Create Date: 2025-04-30 21:45:27.329509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6870016ce725'
down_revision: Union[str, None] = '7d6562db3339'
branch_labels = None
depends_on = None

def upgrade():
    # Добавляем столбцы created и updated в таблицу user_diseases
    op.add_column('user_diseases', sa.Column('created', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.add_column('user_diseases', sa.Column('updated', sa.DateTime(), nullable=False, server_default=sa.func.now()))

def downgrade():
    # Удаляем столбцы created и updated при откате
    op.drop_column('user_diseases', 'updated')
    op.drop_column('user_diseases', 'created')