from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import get_current_user, rate_limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.db.session import SessionLocal
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, dependencies=[Depends(rate_limiter(10, 60))])
async def signup(payload: SignupRequest):
    with SessionLocal() as session:
        existing = session.execute(
            select(User).where(User.email == payload.email.lower())
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists",
            )

        user = User(
            email=payload.email.lower(),
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        user_resp = UserResponse.model_validate(user)
        token = create_access_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=token, user=user_resp)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limiter(10, 60))])
async def login(payload: LoginRequest):
    with SessionLocal() as session:
        user = session.execute(
            select(User).where(User.email == payload.email.lower())
        ).scalar_one_or_none()
        if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        user_resp = UserResponse.model_validate(user)
        token = create_access_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=token, user=user_resp)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
