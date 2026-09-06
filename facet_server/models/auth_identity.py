import datetime
import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from facet_server.models.base import Base
from facet_server.models.facet_user import FacetUser


class AuthIdentity(Base):
    """One auth provider's identifier for a person, linked to the internal `user_id`.

    A row is written only from a signature-verified ID token: a `provider_sub` that arrived as
    a bare value from a client is not an identity and must never reach this table.

    `(provider, provider_sub)` is unique, so looking one up is how a login resolves to a user:
    a hit returns the existing `user_id`, a miss is a person who has not been seen before. One
    user may hold several rows, one per provider.
    """

    __tablename__ = "auth_identity"
    __table_args__ = (UniqueConstraint("provider", "provider_sub"),)

    auth_identity_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facet_user.user_id"),
        nullable=False,
        index=True,
    )

    # The provider that issued `provider_sub`, e.g. "google". Not constrained to a fixed set:
    # adding a provider is a code change, not a migration.
    provider: Mapped[str] = mapped_column(String(32), nullable=False)

    # The provider's permanent identifier for the account, Google's `sub` claim. Stable across
    # a change of name or email on that account.
    provider_sub: Mapped[str] = mapped_column(String(255), nullable=False)

    # The decoded payload of the last verified ID token, stored whole so a claim that was not
    # copied onto `user` is still recoverable and a claim Google adds later needs no migration.
    #
    # The decoded payload only. The token string itself is never stored: it is a bearer
    # credential until it expires, and this row is not the place for one. Written only after the
    # signature check, like every other column here.
    #
    # Null on a row written before this column existed, not on a row that had no claims.
    raw_claims: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # When `raw_claims` and the profile columns on `user` were last refreshed from this provider,
    # which is what says how stale the snapshot is. Distinct from `created_at`, which is when the
    # person first authenticated.
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )

    facet_user: Mapped[FacetUser] = relationship(back_populates="auth_identities")
