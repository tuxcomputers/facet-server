from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Constraint names are generated rather than left to Postgres, so a migration can drop a
# constraint by name and the name is the same in every environment. The shapes follow the
# desktop app's SQLite schema (PK_time_entry, UN1_time_entry).
NAMING_CONVENTION = {
    "pk": "PK_%(table_name)s",
    "uq": "UN_%(table_name)s_%(column_0_N_name)s",
    "ix": "IX_%(table_name)s_%(column_0_N_name)s",
    "fk": "FK_%(table_name)s_%(column_0_N_name)s",
    "ck": "CK_%(table_name)s_%(constraint_name)s",
}


class Base(DeclarativeBase):
    """Declarative base every model inherits from.

    `Base.metadata` is what Alembic autogenerate compares against, so a model that is not
    imported by `facet_server.models` is invisible to it and will be generated as a drop.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
