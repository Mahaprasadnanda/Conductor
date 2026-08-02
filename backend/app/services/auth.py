from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.user import user_repo
from app.schemas.user import UserCreate
from app.models.user import User
from app.auth.security import get_password_hash, verify_password

class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
        existing_user = await user_repo.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
        hashed_password = get_password_hash(user_in.password)
        db_user = User(email=user_in.email, hashed_password=hashed_password)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
        user = await user_repo.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
