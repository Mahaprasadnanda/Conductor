from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.services.auth import AuthService
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db_session)):
    return await AuthService.register_user(db, user_in)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db_session)):
    user = await AuthService.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh-token", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    access_token = create_access_token(subject=current_user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
