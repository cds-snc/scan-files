"""reduce mandatory fields and rely on assemblyline

Revision ID: 693ead1304c2
Revises: fdbf608faf86
Create Date: 2021-11-18 18:47:34.804287

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "693ead1304c2"
down_revision = "fdbf608faf86"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("scans", "submitter", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("scans", "file_size", existing_type=sa.NUMERIC(), nullable=True)
    op.alter_column("scans", "save_path", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("scans", "sha256", existing_type=sa.VARCHAR(), nullable=True)
    # ### end Alembic commands ###


def downgrade():
    op.execute(
        """
        DELETE FROM scans;
        """
    )
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("scans", "sha256", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("scans", "save_path", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("scans", "file_size", existing_type=sa.NUMERIC(), nullable=False)
    op.alter_column("scans", "submitter", existing_type=sa.VARCHAR(), nullable=False)
    # ### end Alembic commands ###
