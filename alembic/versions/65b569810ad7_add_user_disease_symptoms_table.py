"""Add user_disease_symptoms table

Revision ID: 65b569810ad7
Revises: 6870016ce725
Create Date: 2025-05-04 21:29:58.970583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65b569810ad7'
down_revision: Union[str, None] = '6870016ce725'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_disease_symptoms',
    sa.Column('user_disease_id', sa.Integer(), nullable=False),
    sa.Column('symptom_id', sa.Integer(), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['symptom_id'], ['symptoms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_disease_id'], ['user_diseases.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_disease_id', 'symptom_id')
    )
    op.create_index(op.f('ix_user_diseases_id'), 'user_diseases', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_diseases_id'), table_name='user_diseases')
    op.drop_table('user_disease_symptoms')
    # ### end Alembic commands ###
