import asyncio
import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.gateway.cache import service_cache
from app.models.service import ServiceStatus

def test_cache():
    service_cache.set("test", {"status": "Disabled", "base_url": "http://1"})
    service_data = service_cache.get("test")
    
    print("Status in cache:", repr(service_data.get("status")))
    print("Is it in [HEALTHY, UNKNOWN]?", service_data.get("status") in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN])

    service_cache.set("test2", {"status": ServiceStatus.DISABLED, "base_url": "http://1"})
    service_data2 = service_cache.get("test2")
    
    print("Status in cache (ENUM):", repr(service_data2.get("status")))
    print("Is it in [HEALTHY, UNKNOWN]?", service_data2.get("status") in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN])
    
if __name__ == "__main__":
    test_cache()
