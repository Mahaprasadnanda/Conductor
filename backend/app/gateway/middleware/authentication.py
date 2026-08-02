from typing import Optional, Any
from app.gateway.middleware.base import BaseMiddleware
from app.gateway.context import RequestContext
from app.gateway.exceptions import AuthenticationException
from app.gateway.cache import service_cache
from app.models.service import ServiceAuthMode
import jwt
from app.config.settings import settings

class AuthenticationMiddleware(BaseMiddleware):
    async def before_request(self, context: RequestContext) -> None:
        if not context.gateway.service_name:
            return
            
        service_data = service_cache.get(context.gateway.service_name)
        if not service_data:
            return # Let the proxy or another component handle the missing service
            
        auth_mode = service_data.get("authentication_mode", ServiceAuthMode.JWT_REQUIRED)
        
        if auth_mode in (ServiceAuthMode.PUBLIC, ServiceAuthMode.DISABLED):
            return
            
        if auth_mode == ServiceAuthMode.JWT_REQUIRED:
            if not context.fastapi_request:
                raise AuthenticationException("FastAPI request object not provided to context")
                
            auth_header = context.fastapi_request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise AuthenticationException("Missing or invalid authorization header")
                
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                context.auth.authenticated_user = payload.get("sub")
            except Exception as e:
                raise AuthenticationException(f"Invalid token")
                
        elif auth_mode == ServiceAuthMode.API_KEY_REQUIRED:
            raise AuthenticationException("API key authentication not implemented yet")

    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        pass
