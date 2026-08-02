import httpx
from fastapi import Response

class ResponseBuilder:
    @staticmethod
    def build(httpx_response: httpx.Response) -> Response:
        headers = {k: v for k, v in httpx_response.headers.items() 
                   if k.lower() not in ('content-length', 'content-encoding', 'transfer-encoding')}
        return Response(
            content=httpx_response.content,
            status_code=httpx_response.status_code,
            headers=headers
        )
