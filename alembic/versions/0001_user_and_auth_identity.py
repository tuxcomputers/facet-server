"""user and auth_identity

Revision ID: 0001
Revises:
Create Date: 2026-09-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "facet_user",
        sa.Column(
            "user_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "daily_reset_time",
            sa.Time(),
            server_default=sa.text("'03:00:00'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("PK_facet_user")),
    )
    op.create_table(
        "auth_identity",
        sa.Column(
            "auth_identity_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_sub", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["facet_user.user_id"],
            name=op.f("FK_auth_identity_user_id"),
        ),
        sa.PrimaryKeyConstraint("auth_identity_id", name=op.f("PK_auth_identity")),
        sa.UniqueConstraint(
            "provider",
            "provider_sub",
            name=op.f("UN_auth_identity_provider_provider_sub"),
        ),
    )
    op.create_index(
        op.f("IX_auth_identity_user_id"),
        "auth_identity",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("IX_auth_identity_user_id"), table_name="auth_identity")
    op.drop_table("auth_identity")
    op.drop_table("facet_user")
