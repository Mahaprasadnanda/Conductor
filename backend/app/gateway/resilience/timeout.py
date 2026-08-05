from app.gateway.context import RequestContext

class TimeoutPolicy:
    @staticmethod
    def apply(context: RequestContext, timeout_seconds: int) -> None:
        """
        Applies the configured timeout to the request context.
        The ProxyEngine will read this value.
        """
        context.resilience.timeout = float(timeout_seconds)
