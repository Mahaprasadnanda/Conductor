from abc import ABC, abstractmethod
from typing import Optional, Any
from app.gateway.context import RequestContext

class BaseMiddleware(ABC):
    @abstractmethod
    async def before_request(self, context: RequestContext) -> None:
        """
        Executed before the proxy forwards the request.
        Raise GatewayException (or its subclasses) if the request should be aborted.
        """
        pass

    @abstractmethod
    async def after_response(self, context: RequestContext, response: Optional[Any]) -> None:
        """
        Executed after the proxy returns a response (or if an exception occurred in the proxy).
        If the proxy failed, response may be None.
        """
        pass
