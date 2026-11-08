"""Owner bootstrap, login, session inspection, and logout endpoints."""
import secrets
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, hash_password, verify_password, get_current_user
from app.core.config import settings
from app.db.models import UserModel
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class BootstrapRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=12, max_length=256)

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)

def _public_user(user: UserModel) -> dict:
    return {"id": user.id, "username": user.username, "role": user.role, "created_at": user.created_at}

@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
def bootstrap_owner(request: BootstrapRequest, bootstrap_secret: str = Header("", alias="X-Nexus-Bootstrap-Secret"), db: Session = Depends(get_db)):
    configured = settings.AUTH_BOOTSTRAP_SECRET
    if not configured or len(configured) < 24 or not secrets.compare_digest(bootstrap_secret, configured):
        raise HTTPException(status_code=403, detail="Invalid or unavailable bootstrap secret.")
    if db.query(UserModel).count() != 0:
        raise HTTPException(status_code=409, detail="Bootstrap is already complete.")
    if db.query(UserModel).filter(UserModel.username == request.username).first():
        raise HTTPException(status_code=409, detail="Username is already registered.")
    user = UserModel(id=str(uuid.uuid4()), username=request.username, role="owner", password_hash=hash_password(request.password), is_active=True, token_version=0, created_at=datetime.now(timezone.utc))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user": _public_user(user), "access_token": create_access_token(user), "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_TTL_MINUTES * 60}

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == request.username).first()
    if not user or not user.is_active or not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.", headers={"WWW-Authenticate": "Bearer"})
    return {"user": _public_user(user), "access_token": create_access_token(user), "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_TTL_MINUTES * 60}

@router.get("/me")
def who_am_i(user: UserModel = Depends(get_current_user)):
    return _public_user(user)

@router.post("/logout")
def logout(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    user.token_version += 1
    db.add(user)
    db.commit()
    return {"status": "logged_out"}
