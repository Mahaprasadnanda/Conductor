import urllib.request, json
import time

def run():
    # register user
    req = urllib.request.Request('http://localhost:8000/api/v1/auth/register', data=b'{"email":"test_live@test.com","password":"admin"}', headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except:
        pass

    req = urllib.request.Request('http://localhost:8000/api/v1/auth/login', data=b'username=test_live%40test.com&password=admin', headers={'Content-Type': 'application/x-www-form-urlencoded'})
    token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']
    auth_header = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}

    req = urllib.request.Request('http://localhost:8000/api/v1/projects/', data=b'{"name":"proj1"}', headers=auth_header)
    proj_id = json.loads(urllib.request.urlopen(req).read().decode())['id']

    req = urllib.request.Request(f'http://localhost:8000/api/v1/services/?project_id={proj_id}', data=b'{"service_name":"live_svc","base_url":"http://localhost:8000/docs","is_active":true,"strip_path":false,"load_balancer_strategy":"ROUND_ROBIN"}', headers=auth_header)
    svc_id = json.loads(urllib.request.urlopen(req).read().decode())['id']

    req = urllib.request.Request('http://localhost:8000/api/v1/service-instances/', data=('{"service_id":' + str(svc_id) + ',"base_url":"http://localhost:8000","status":"Healthy"}').encode(), headers=auth_header)
    urllib.request.urlopen(req)

    print('Service created! Now waiting 12s for cache sync')
    time.sleep(12)

    try:
        req = urllib.request.Request('http://localhost:8000/api/v1/gateway/live_svc/docs', headers=auth_header)
        urllib.request.urlopen(req)
    except Exception as e:
        print('Gateway error:', e)

    metrics = urllib.request.urlopen('http://localhost:8000/metrics').read().decode()
    for line in metrics.splitlines():
        if "gateway_" in line and not line.startswith("#"):
            print(line)

run()
