from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """
    Simple liveness check. Returns 200 with a small JSON body if the
    app is up and able to handle requests at all — no DB or LLM
    checks yet, those come once those dependencies exist.
    """
    return {"status": "ok"}
