import httpx
from app.gateway.context import RequestContext
from app.gateway.proxy.request_builder import RequestBuilder
from app.gateway.proxy.response_builder import ResponseBuilder
from app.gateway.exceptions import ProxyException

class ProxyEngine:
    @staticmethod
    async def forward(context: RequestContext):
        request = await RequestBuilder.build(context)
        
        # Use dynamic timeout from resilience context, default to 30.0 if not available
        timeout = context.resilience.timeout if context.resilience.timeout else 30.0
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.send(request)
            except Exception as e:
                raise ProxyException(f"Failed to forward request: {str(e)}")
                
        # Populate context with response data
        context.gateway.response_status = response.status_code
        context.gateway.response_size = len(response.content)
        
        fastapi_response = ResponseBuilder.build(response)
        context.fastapi_response = fastapi_response
        return fastapi_response
