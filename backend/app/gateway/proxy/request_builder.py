import httpx
from urllib.parse import urlencode
from app.gateway.context import RequestContext

class RequestBuilder:
    @staticmethod
    async def build(context: RequestContext) -> httpx.Request:
        base_url = context.custom.metadata.get("target_base_url")
        if not base_url:
            from app.gateway.exceptions import ProxyException
            raise ProxyException("Target base URL not found in request context")
            
        target_url = f"{base_url}/{context.gateway.path}"
        if context.gateway.query_params:
            target_url = f"{target_url}?{urlencode(context.gateway.query_params)}"
            
        headers = dict(context.gateway.headers)
        headers.pop("host", None)

        body = None
        if context.fastapi_request:
            body = await context.fastapi_request.body()

        return httpx.Request(
            method=context.gateway.method,
            url=target_url,
            headers=headers,
            content=body
        )
