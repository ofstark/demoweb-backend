from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.config import settings
from app.deps import get_current_user
from app.services.auth import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    valid_user = payload.username.strip().lower() == settings.astra_username.strip().lower()
    valid_password = verify_password(payload.password, settings.astra_password_hash)

    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(subject=settings.astra_username)
    return TokenResponse(access_token=token, username=settings.astra_username)


@router.get("/me")
async def me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}
