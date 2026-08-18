from typing import Optional, Any
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.gateway.exceptions import AuthenticationException
from app.gateway.cache import service_cache
from app.models.service import ServiceAuthMode
import jwt
from app.config.settings import settings

import hashlib
from app.repositories.api_key import api_key_repo

class AuthenticationMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        if not context.gateway.service_name:
            return
            
        service_data = service_cache.get(context.gateway.service_name)
        if not service_data:
            return
            
        auth_mode = service_data.get("authentication_mode", ServiceAuthMode.JWT_REQUIRED)
        
        if auth_mode in (ServiceAuthMode.PUBLIC, ServiceAuthMode.DISABLED):
            return
            
        if not context.fastapi_request:
            raise AuthenticationException("FastAPI request object not provided to context")
            
        auth_header = context.fastapi_request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationException("Missing or invalid authorization header")
            
        token = auth_header.split(" ")[1]
            
        if auth_mode == ServiceAuthMode.JWT_REQUIRED:
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                context.auth.authenticated_user = payload.get("sub")
            except Exception as e:
                raise AuthenticationException(f"Invalid token")
                
        elif auth_mode == ServiceAuthMode.API_KEY_REQUIRED:
            from app.database.connection import async_session_maker
            
            key_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            async with async_session_maker() as db:
                api_key = await api_key_repo.get_by_hash(db, key_hash)
                
            if not api_key:
                raise AuthenticationException("Invalid or revoked API key")
                
            if api_key.project_id != service_data.get("project_id"):
                raise AuthenticationException("API key is not authorized for this service")
                
            context.auth.authenticated_project = api_key.project_id
            
            # Prevent API key from leaking to the upstream service
            if "authorization" in context.gateway.headers:
                del context.gateway.headers["authorization"]
            if "Authorization" in context.gateway.headers:
                del context.gateway.headers["Authorization"]

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        pass
