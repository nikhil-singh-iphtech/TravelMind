import logging
from sqlalchemy import select

from app.db.models.planning_run import PlanningRun
from app.db.session import SessionLocal
from app.schemas.state import TravelRequest, TravelState

logger = logging.getLogger(__name__)


class RunPersistenceService:
    """Saves and retrieves planning runs for user history and persistence."""

    def save_run(
        self,
        *,
        run_id: str,
        user_id: int,
        request: TravelRequest,
        state: TravelState,
    ) -> None:
        try:
            with SessionLocal() as session:
                existing = session.execute(
                    select(PlanningRun).where(PlanningRun.run_id == run_id)
                ).scalar_one_or_none()

                request_dict = request.model_dump(mode="json")
                state_dict = state.model_dump(mode="json")
                events_list = [e.model_dump(mode="json") for e in state.events]

                if existing:
                    existing.status = state.status
                    existing.iteration = state.iteration
                    existing.result_data = state_dict
                    existing.events_data = events_list
                else:
                    run_record = PlanningRun(
                        run_id=run_id,
                        user_id=user_id,
                        status=state.status,
                        iteration=state.iteration,
                        request_data=request_dict,
                        result_data=state_dict,
                        events_data=events_list,
                    )
                    session.add(run_record)
                session.commit()
                logger.info("Persisted planning run=%s for user_id=%s status=%s", run_id, user_id, state.status)
        except Exception as exc:
            logger.error("Failed to persist planning run=%s: %s", run_id, exc, exc_info=True)

    def get_run(self, run_id: str, user_id: int) -> dict | None:
        with SessionLocal() as session:
            run = session.execute(
                select(PlanningRun).where(PlanningRun.run_id == run_id, PlanningRun.user_id == user_id)
            ).scalar_one_or_none()

            if not run:
                return None

            return {
                "id": run.id,
                "run_id": run.run_id,
                "user_id": run.user_id,
                "status": run.status,
                "iteration": run.iteration,
                "request": run.request_data,
                "result": run.result_data,
                "events": run.events_data or [],
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }

    def list_user_runs(self, user_id: int, limit: int = 20) -> list[dict]:
        with SessionLocal() as session:
            runs = session.execute(
                select(PlanningRun)
                .where(PlanningRun.user_id == user_id)
                .order_by(PlanningRun.created_at.desc())
                .limit(limit)
            ).scalars().all()

            results = []
            for r in runs:
                req = r.request_data or {}
                results.append({
                    "id": r.id,
                    "run_id": r.run_id,
                    "user_id": r.user_id,
                    "status": r.status,
                    "destination": req.get("destination", "Unknown"),
                    "origin": req.get("origin", ""),
                    "start_date": req.get("start_date"),
                    "budget": req.get("budget"),
                    "currency": req.get("currency", "INR"),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                })
            return results
    def get_public_run(self, run_id: str) -> dict | None:
        with SessionLocal() as session:
            run = session.execute(
                select(PlanningRun).where(PlanningRun.run_id == run_id)
            ).scalar_one_or_none()

            if not run:
                return None

            return {
                "id": run.id,
                "run_id": run.run_id,
                "user_id": run.user_id,
                "status": run.status,
                "iteration": run.iteration,
                "request": run.request_data,
                "result": run.result_data,
                "events": run.events_data or [],
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
