from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import settings
from app.database.connection import get_db_session
from app.models.user import User
from app.repositories.user import user_repo
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login", auto_error=False)

async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
        
    user = await user_repo.get(db, id=int(token_data.sub))
    if user is None:
        raise credentials_exception
    return user
