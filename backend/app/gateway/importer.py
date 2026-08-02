import httpx
from fastapi import HTTPException, status
from app.schemas.endpoint import EndpointCreate
import structlog

log = structlog.get_logger()

class OpenAPIImporter:
    @staticmethod
    async def fetch_and_parse(openapi_url: str) -> list[EndpointCreate]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(openapi_url)
                response.raise_for_status()
                spec = response.json()
            except Exception as e:
                log.error("openapi_fetch_failed", url=openapi_url, error=str(e))
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to fetch OpenAPI spec: {e}")

        endpoints = []
        paths = spec.get("paths", {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() not in ["get", "post", "put", "patch", "delete", "options", "head"]:
                    continue
                    
                endpoints.append(EndpointCreate(
                    path=path,
                    method=method.upper(),
                    operation_id=operation.get("operationId"),
                    summary=operation.get("summary"),
                    description=operation.get("description"),
                    tags=operation.get("tags", []),
                    request_body=operation.get("requestBody"),
                    response_defs=operation.get("responses")
                ))
        return endpoints
