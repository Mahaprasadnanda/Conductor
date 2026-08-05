from typing import Optional

class GatewayException(Exception):
    def __init__(self, message: str, status_code: int = 500, headers: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}

class AuthenticationException(GatewayException):
    def __init__(self, message: str = "Authentication failed", status_code: int = 401):
        super().__init__(message, status_code)

class ServiceUnavailableException(GatewayException):
    def __init__(self, message: str = "Service unavailable", status_code: int = 503):
        super().__init__(message, status_code)

class ProxyException(GatewayException):
    def __init__(self, message: str = "Bad Gateway", status_code: int = 502):
        super().__init__(message, status_code)

class MiddlewareException(GatewayException):
    def __init__(self, message: str = "Middleware error", status_code: int = 500):
        super().__init__(message, status_code)

class RateLimitException(GatewayException):
    def __init__(self, message: str = "Rate limit exceeded", status_code: int = 429, headers: Optional[dict] = None):
        super().__init__(message, status_code, headers)
