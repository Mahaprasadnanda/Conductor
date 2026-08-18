import urllib.request, json, time, urllib.parse

# 8:59 PM in the user's timezone is roughly 1786979940 UTC if they are at +5:30.
# Actually let's just query the last 2 hours to be sure.
now = int(time.time())
start = now - 7200
end = now
step = '1m'
query = 'histogram_quantile(0.95, sum(rate(gateway_request_latency_seconds_bucket{project_id="26"}[5m])) by (le))'
url = f'http://prometheus:9090/api/v1/query_range?query={urllib.parse.quote(query)}&start={start}&end={end}&step={step}'

try:
    res = urllib.request.urlopen(url).read().decode()
    data = json.loads(res)['data']['result']
    if data:
        values = data[0]['values']
        print(f"Total points: {len(values)}")
        print("Non-NaN points:")
        for pt in values:
            if pt[1] != 'NaN':
                print(pt)
    else:
        print('No data')
except Exception as e:
    print(f"Error: {e}")
