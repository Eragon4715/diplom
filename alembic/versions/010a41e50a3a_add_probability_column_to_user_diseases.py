"""Add probability column to user_diseases

Revision ID: 010a41e50a3a
Revises: 6cc4747ff5c0
Create Date: 2025-04-23 13:20:21.689365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010a41e50a3a'
down_revision: Union[str, None] = '6cc4747ff5c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_diseases', sa.Column('probability', sa.Float(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_diseases', 'probability')
    # ### end Alembic commands ###
