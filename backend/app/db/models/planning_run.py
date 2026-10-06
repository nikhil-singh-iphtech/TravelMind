from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class PlanningRun(Base):
    __tablename__ = "planning_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    travel_request_id: Mapped[int] = mapped_column(ForeignKey("travel_requests.id"))

    status: Mapped[str] = mapped_column(String(50), default="pending")
    # pending → running → completed / failed

    iteration: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )