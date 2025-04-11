"""Add age to users and weight to disease_symptoms

Revision ID: 782bb4a05d1c
Revises: 89cd97ef565f
Create Date: 2025-04-11 18:04:44.047694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '782bb4a05d1c'
down_revision: Union[str, None] = '89cd97ef565f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('disease_symptoms', sa.Column('weight', sa.Float(), nullable=False))
    op.alter_column('health_metrics', 'created',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'age')
    op.alter_column('health_metrics', 'created',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.drop_column('disease_symptoms', 'weight')
    # ### end Alembic commands ###
