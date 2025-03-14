"""Add all models

Revision ID: 1a228aa54a6f
Revises: d27fee32fef3
Create Date: 2025-02-02 20:52:08.770124

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a228aa54a6f'
down_revision: Union[str, None] = 'd27fee32fef3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('symptoms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_symptoms_id'), 'symptoms', ['id'], unique=False)
    op.create_index(op.f('ix_symptoms_name'), 'symptoms', ['name'], unique=True)
    op.create_table('disease_symptoms',
    sa.Column('disease_id', sa.Integer(), nullable=False),
    sa.Column('symptom_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['symptom_id'], ['symptoms.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('disease_id', 'symptom_id')
    )
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'nickname',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'nickname',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_table('disease_symptoms')
    op.drop_index(op.f('ix_symptoms_name'), table_name='symptoms')
    op.drop_index(op.f('ix_symptoms_id'), table_name='symptoms')
    op.drop_table('symptoms')
    # ### end Alembic commands ###
