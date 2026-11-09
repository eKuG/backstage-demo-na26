import sys, json, urllib.request, urllib.parse, time
q = sys.argv[1]; now = int(time.time())
u = "http://localhost:3200/api/search?" + urllib.parse.urlencode({"q": q, "limit": 5, "start": now-600, "end": now})
ts = json.load(urllib.request.urlopen(u)).get("traces", [])
best = None
for t in ts:
    d = json.load(urllib.request.urlopen(f"http://localhost:3200/api/traces/{t['traceID']}"))
    n = sum(len(ss["spans"]) for b in d.get("batches", []) for ss in b["scopeSpans"])
    if best is None or n > best[1]: best = (t["traceID"], n)
print(best[0] if best else "", best[1] if best else 0)
