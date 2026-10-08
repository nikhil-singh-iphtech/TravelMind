import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_sse_stream_handles_error_gracefully(monkeypatch):
    async def mock_run_failing(*args, **kwargs):
        raise RuntimeError("Simulated Database Connection Failure")

    monkeypatch.setattr(
        "app.orchestration.custom.orchestrator.TravelOrchestrator.run",
        mock_run_failing,
    )

    from app.api.dependencies import get_current_user
    from app.db.models.user import User

    app.dependency_overrides[get_current_user] = lambda: User(id=1, email="test@example.com", password_hash="pw")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "trip": {
                "origin": "DEL",
                "destination": "TYO",
                "start_date": "2026-11-01",
                "duration_days": 7,
                "budget": 200000,
                "currency": "INR",
                "travellers": 2,
                "interests": ["culture"],
            },
            "user_id": 1,
            "engine": "custom",
        }
        response = await ac.post("/travel-plans/stream", json=payload)
        assert response.status_code == 200
        content = response.text
        assert "event: error" in content
        assert "Planning failed" in content
        assert "Simulated Database Connection Failure" not in content