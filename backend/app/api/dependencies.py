import time
from collections import defaultdict
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import SessionLocal

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        # Detach instance before returning from session context
        session.expunge(user)
        return user


# In-memory simple rate limiter (e.g. 20 requests per minute per IP)
_rate_limit_records = defaultdict(list)


def rate_limiter(max_requests: int = 20, window_seconds: int = 60):
    async def limit_checker(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        timestamps = _rate_limit_records[client_ip]
        # Purge timestamps outside current window
        _rate_limit_records[client_ip] = [t for t in timestamps if now - t < window_seconds]
        if len(_rate_limit_records[client_ip]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before retrying.",
            )
        _rate_limit_records[client_ip].append(now)

    return limit_checker