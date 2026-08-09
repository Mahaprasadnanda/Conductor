import urllib.request
import json
import time
import random

def run():
    # Register user
    try:
        req = urllib.request.Request('http://localhost:8000/api/v1/auth/register', data=b'{"email":"admin@example.com","password":"adminpassword"}', headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req)
    except:
        pass

    # Login
    req = urllib.request.Request('http://localhost:8000/api/v1/auth/login', data=b'username=admin%40example.com&password=adminpassword', headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        res = urllib.request.urlopen(req)
        token = json.loads(res.read().decode())['access_token']
    except Exception as e:
        print("Login failed, ensure backend is up:", e)
        return
        
    auth_header = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    
    # Try to query gateway
    for i in range(10):
        try:
            url = 'http://localhost:8000/api/v1/gateway/demo/hello'
            if random.random() < 0.2:
                # Force an error by going to a bad endpoint
                url = 'http://localhost:8000/api/v1/gateway/demo/nonexistent'
                
            req = urllib.request.Request(url, headers=auth_header)
            urllib.request.urlopen(req)
            print(f"[{i}] Success")
        except Exception as e:
            print(f"[{i}] Gateway returned:", getattr(e, 'code', 'error'))
            
        time.sleep(0.5)

if __name__ == '__main__':
    run()
