"""Change user_diseases to allow multiple entries

   Revision ID: 7d6562db3339
   Revises: 0f740ebb5890
   Create Date: 2025-04-30 12:46:00.000000

   """
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7d6562db3339'
down_revision = '0f740ebb5890'
branch_labels = None
depends_on = None

def upgrade():
    # Удаляем старую таблицу (данных нет, поэтому перенос не нужен)
    op.drop_table('user_diseases')

    # Создаём новую таблицу user_diseases с новым первичным ключом
    op.create_table(
        'user_diseases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('disease_id', sa.Integer(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('prediction_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Удаляем новую таблицу
    op.drop_table('user_diseases')

    # Восстанавливаем старую структуру таблицыы user_diseases
    op.create_table(
        'user_diseases',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('disease_id', sa.Integer(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('prediction_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'disease_id')
    )