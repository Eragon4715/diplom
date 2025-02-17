"""initial migration1

Revision ID: e39a02a26d90
Revises: 1730344ca1d2
Create Date: 2025-01-28 20:58:52.000425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e39a02a26d90'
down_revision: Union[str, None] = '1730344ca1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nickname', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('surname', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_online', sa.Boolean(), nullable=False),
    sa.Column('imageURL', sa.String(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_is_online'), 'users', ['is_online'], unique=False)
    op.create_index(op.f('ix_users_nickname'), 'users', ['nickname'], unique=True)
    op.drop_index('ix_user_tg_id', table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('tg_id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('fio', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('lvl', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('taps_for_level', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('is_admin', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('is_banned', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('money', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('current_factor', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('invited_tg_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('last_login', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('received_last_daily_reward', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('days_in_row', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('number_of_columns_passed', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('is_premium', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('created', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['invited_tg_id'], ['user.tg_id'], name='user_invited_tg_id_fkey'),
    sa.PrimaryKeyConstraint('tg_id', name='user_pkey')
    )
    op.create_index('ix_user_tg_id', 'user', ['tg_id'], unique=True)
    op.drop_index(op.f('ix_users_nickname'), table_name='users')
    op.drop_index(op.f('ix_users_is_online'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
