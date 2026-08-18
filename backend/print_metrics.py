import urllib.request

try:
    with urllib.request.urlopen("http://localhost:8000/metrics") as response:
        html = response.read().decode()
        for line in html.split('\n'):
            if "gateway_request_latency_seconds_bucket" in line:
                print(line)
except Exception as e:
    print(e)
