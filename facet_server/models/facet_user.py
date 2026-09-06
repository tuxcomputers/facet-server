import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text, Time, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from facet_server.models.base import Base

if TYPE_CHECKING:
    from facet_server.models.auth_identity import AuthIdentity


class FacetUser(Base):
    """One person, keyed by a `user_id` that no auth provider owns.

    A Google `sub` is not a column here: it is a row in `auth_identity`, so a second provider
    later adds a row rather than a column.

    Every profile column is a snapshot of what the provider returned at the last login, and none
    of them is an identity that may be matched on: all of them can change at the provider without
    the `sub` changing, and any of them can be null where the scope was not granted. The claims
    they are copied from are kept verbatim in `auth_identity.raw_claims`.
    """

    __tablename__ = "facet_user"

    user_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # Deliberately not unique: two rows sharing an email is a state to detect and resolve, not
    # one for the database to refuse, and refusing it would make the email an identity.
    email: Mapped[str | None] = mapped_column(String(320))

    # Google's `email_verified`. Three-valued on purpose: null is "never told", which is not the
    # same as false, and a check for verified must not read a null as either.
    email_verified: Mapped[bool | None] = mapped_column(Boolean)

    # Google's `name`, `given_name` and `family_name`. `display_name` is what Google renders the
    # person as, and is not always the other two joined.
    display_name: Mapped[str | None] = mapped_column(String(255))
    given_name: Mapped[str | None] = mapped_column(String(255))
    family_name: Mapped[str | None] = mapped_column(String(255))

    # Google's `picture`, a URL to an image hosted by Google, not the image.
    picture_url: Mapped[str | None] = mapped_column(Text)

    # Google's `hd`, the Workspace domain the account belongs to. Null for a personal account,
    # which is what makes it worth keeping: it is how a work account is told from a personal one.
    hosted_domain: Mapped[str | None] = mapped_column(String(255))

    # Google's `locale`, a BCP 47 tag such as "en-AU". Not a timezone, and not usable as one.
    locale: Mapped[str | None] = mapped_column(String(35))

    # Wall-clock time of day at which this person's day rolls over, mirroring the app's
    # `daily_reset_time` setting (seeded there to 03:00, so a session spanning midnight is not
    # split). TIME WITHOUT TIME ZONE is deliberate: this is a setting, not an instant, so the
    # rule that instants carry their zone does not apply. It is resolved against the zone the
    # entry being grouped carries. Applies only to reports grouped by this person; a report
    # across a team uses absolute spans.
    daily_reset_time: Mapped[datetime.time] = mapped_column(
        Time(timezone=False),
        nullable=False,
        server_default=text("'03:00:00'"),
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )

    auth_identities: Mapped[list["AuthIdentity"]] = relationship(back_populates="facet_user")
