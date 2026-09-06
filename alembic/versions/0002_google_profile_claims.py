"""google profile claims

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-05 10:15:16.613366

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "auth_identity",
        sa.Column("raw_claims", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "auth_identity",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column("facet_user", sa.Column("email_verified", sa.Boolean(), nullable=True))
    op.add_column("facet_user", sa.Column("given_name", sa.String(length=255), nullable=True))
    op.add_column("facet_user", sa.Column("family_name", sa.String(length=255), nullable=True))
    op.add_column("facet_user", sa.Column("picture_url", sa.Text(), nullable=True))
    op.add_column("facet_user", sa.Column("hosted_domain", sa.String(length=255), nullable=True))
    op.add_column("facet_user", sa.Column("locale", sa.String(length=35), nullable=True))


def downgrade() -> None:
    op.drop_column("facet_user", "locale")
    op.drop_column("facet_user", "hosted_domain")
    op.drop_column("facet_user", "picture_url")
    op.drop_column("facet_user", "family_name")
    op.drop_column("facet_user", "given_name")
    op.drop_column("facet_user", "email_verified")
    op.drop_column("auth_identity", "updated_at")
    op.drop_column("auth_identity", "raw_claims")
