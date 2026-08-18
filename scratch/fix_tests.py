import os
import re

TESTS_DIR = "backend/tests"

# Files that need fixing
files = [
    "test_load_balancer.py",
    "test_metrics.py",
    "test_middleware.py",
    "test_rate_limit.py",
    "test_resilience.py",
    "test_services.py"
]

def fix_test_file(filename):
    path = os.path.join(TESTS_DIR, filename)
    with open(path, "r") as f:
        content = f.read()
    
    # 1. Fix async_client.post("/api/v1/services/"
    # If the file already creates a project, use its ID or hardcode 1.
    # In many files we don't have project creation yet.
    if "async_client.post(\"/api/v1/projects/\"" not in content:
        # Add project creation before the first service creation
        content = re.sub(
            r'(res = await async_client\.post\(\s*"/api/v1/services/"|await async_client\.post\(\s*"/api/v1/services/")',
            r'await async_client.post("/api/v1/projects/", json={"name": "Test Project"}, headers=auth_headers)\n    \g<1>',
            content,
            count=1
        )
    
    # Replace /api/v1/services/ with /api/v1/services/?project_id=1
    content = content.replace('"/api/v1/services/"', '"/api/v1/services/?project_id=1"')
    
    # 2. Fix DB inserts
    # Service(service_name="...", ...) -> Service(service_name="...", project_id=1, ...)
    content = re.sub(
        r'Service\(\s*service_name',
        r'Service(project_id=1, service_name',
        content
    )
    
    # Also we need to make sure project 1 exists in DB for DB tests
    # We can add an autouse fixture in conftest.py instead of modifying all DB tests.
    
    with open(path, "w") as f:
        f.write(content)

for file in files:
    fix_test_file(file)

print("Tests updated.")
