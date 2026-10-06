from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared base class for all SQLAlchemy models.

    Every model (User, TravelRequest, PlanningRun, ...) inherits
    from this. Alembic points at Base.metadata to know what tables
    should exist.
    """
    pass