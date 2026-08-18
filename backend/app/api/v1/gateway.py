from fastapi import APIRouter, Request, Depends
from app.gateway.context import RequestContext
from app.gateway.pipeline import GatewayPipeline
from app.gateway.proxy.proxy import ProxyEngine
from app.gateway.cache import service_cache
from app.models.service import ServiceStatus
from app.gateway.exceptions import ServiceUnavailableException
from app.auth.dependencies import oauth2_scheme

router = APIRouter()
pipeline = GatewayPipeline()

async def _execute_proxy_gateway(service_name: str, path: str, request: Request):
    service_data = service_cache.get(service_name)
    if not service_data:
        raise ServiceUnavailableException(f"Service {service_name} not found in registry", status_code=404)

    context = RequestContext.create()
    context.gateway.service_name = service_name
    context.gateway.service_id = service_data.get("id")
    context.gateway.path = path
    context.gateway.method = request.method
    context.gateway.query_params = dict(request.query_params)
    context.gateway.headers = dict(request.headers)
    context.gateway.client_ip = request.client.host if request.client else None
    context.fastapi_request = request
    
    base_url = service_data["base_url"].rstrip("/")
    context.custom.metadata["target_base_url"] = base_url
    context.custom.metadata["service_data"] = service_data

    # Execute pipeline
    return await pipeline.execute(context, ProxyEngine.forward)

@router.get("/{service_name}/{path:path}", include_in_schema=True)
async def proxy_gateway_get(service_name: str, path: str, request: Request):
    return await _execute_proxy_gateway(service_name, path, request)

@router.post("/{service_name}/{path:path}", include_in_schema=True)
async def proxy_gateway_post(service_name: str, path: str, request: Request):
    return await _execute_proxy_gateway(service_name, path, request)

@router.put("/{service_name}/{path:path}", include_in_schema=True)
async def proxy_gateway_put(service_name: str, path: str, request: Request):
    return await _execute_proxy_gateway(service_name, path, request)

@router.patch("/{service_name}/{path:path}", include_in_schema=True)
async def proxy_gateway_patch(service_name: str, path: str, request: Request):
    return await _execute_proxy_gateway(service_name, path, request)

@router.delete("/{service_name}/{path:path}", include_in_schema=True)
async def proxy_gateway_delete(service_name: str, path: str, request: Request):
    return await _execute_proxy_gateway(service_name, path, request)

@router.options("/{service_name}/{path:path}", include_in_schema=True)
async def proxy_gateway_options(service_name: str, path: str, request: Request):
    return await _execute_proxy_gateway(service_name, path, request)

@router.head("/{service_name}/{path:path}", include_in_schema=True)
async def proxy_gateway_head(service_name: str, path: str, request: Request):
    return await _execute_proxy_gateway(service_name, path, request)
