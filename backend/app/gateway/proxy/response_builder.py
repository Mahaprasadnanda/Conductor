import httpx
from fastapi import Response


class ResponseBuilder:
    # These headers describe how an HTTP connection or response body was
    # transported. The proxy returns a materialized body, so forwarding them
    # can make clients interpret the body with stale compression/chunking
    # metadata.
    EXCLUDED_HEADERS = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
        "content-length",
        "content-encoding",
    }

    @staticmethod
    def build(httpx_response: httpx.Response) -> Response:
        headers = {
            key: value
            for key, value in httpx_response.headers.items()
            if key.lower() not in ResponseBuilder.EXCLUDED_HEADERS
        }

        # HTTPX exposes response.content as the body after content decoding.
        # Do not forward Content-Encoding/Content-Length from the upstream;
        # Starlette will generate correct metadata for the bytes we return.
        return Response(
            content=httpx_response.content,
            status_code=httpx_response.status_code,
            headers=headers,
        )
