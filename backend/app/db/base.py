from app.db.session import engine, Base
from app.db.models.user import User  # noqa
from app.db.models.planning_run import PlanningRun  # noqa
from app.db.models.document_chunk import DocumentChunk  # noqa
from app.db.models.booking import Booking  # noqa

def init_db():
    Base.metadata.create_all(bind=engine)