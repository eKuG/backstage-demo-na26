#!/usr/bin/env python3
"""Generates dashboards/backstage-product.json. Run after changing panels: python3 gen_dashboard.py"""
import json, os

PROM = {"type": "prometheus", "uid": "prometheus"}
LOKI = {"type": "loki", "uid": "loki"}
TEMPO = {"type": "tempo", "uid": "tempo"}
PYRO = {"type": "grafana-pyroscope-datasource", "uid": "pyroscope"}

panels = []
_id = [0]
_y = [0]

def nid():
    _id[0] += 1
    return _id[0]

def row(title):
    panels.append({"type": "row", "title": title, "id": nid(), "collapsed": False,
                   "gridPos": {"x": 0, "y": _y[0], "w": 24, "h": 1}})
    _y[0] += 1

def place(w, h, cursor):
    x = cursor[0]
    if x + w > 24:
        x = 0; cursor[1] += cursor[2]; cursor[2] = 0
    gp = {"x": x, "y": _y[0] + cursor[1], "w": w, "h": h}
    cursor[0] = x + w; cursor[2] = max(cursor[2], h)
    return gp

def base(ptype, title, gp, ds, targets, unit=None, desc="", **extra):
    p = {"type": ptype, "title": title, "id": nid(), "gridPos": gp, "datasource": ds,
         "targets": targets, "description": desc,
         "fieldConfig": {"defaults": {"unit": unit} if unit else {}, "overrides": []},
         "options": {}}
    p.update(extra)
    return p

def prom(exprs, instant=False, fmt="time_series"):
    out = []
    for i, (expr, legend) in enumerate(exprs):
        out.append({"refId": chr(65 + i), "datasource": PROM, "expr": expr, "legendFormat": legend,
                    "instant": instant, "range": not instant, "format": fmt})
    return out

class Grid:
    def __init__(self):
        self.c = [0, 0, 0]
    def ts(self, title, exprs, w=8, h=7, unit=None, desc="", stack=False, maxv=None):
        p = base("timeseries", title, place(w, h, self.c), PROM, prom(exprs), unit, desc)
        p["options"] = {"legend": {"displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}}
        p["fieldConfig"]["defaults"]["custom"] = {"lineWidth": 2, "fillOpacity": 12, "stacking": {"mode": "normal" if stack else "none"}}
        if maxv is not None: p["fieldConfig"]["defaults"]["max"] = maxv; p["fieldConfig"]["defaults"]["min"] = 0
        panels.append(p)
    def stat(self, title, expr, w=4, h=4, unit=None, desc="", thresholds=None, decimals=None):
        p = base("stat", title, place(w, h, self.c), PROM, prom([(expr, "")], instant=True), unit, desc)
        p["options"] = {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "value", "graphMode": "none", "textMode": "value"}
        if thresholds:
            p["fieldConfig"]["defaults"]["thresholds"] = {"mode": "absolute", "steps": thresholds}
        if decimals is not None: p["fieldConfig"]["defaults"]["decimals"] = decimals
        panels.append(p)
    def bar(self, title, expr, w=8, h=7, unit=None, desc="", legend=""):
        p = base("bargauge", title, place(w, h, self.c), PROM, prom([(expr, legend)], instant=True), unit, desc)
        p["options"] = {"reduceOptions": {"calcs": ["lastNotNull"]}, "orientation": "horizontal", "displayMode": "gradient", "showUnfilled": True}
        panels.append(p)
    def table(self, title, expr, w=12, h=8, unit=None, desc="", hide=("Time",), rename=None, sort=None):
        p = base("table", title, place(w, h, self.c), PROM, prom([(expr, "")], instant=True, fmt="table"), unit, desc)
        tr = [{"id": "organize", "options": {"excludeByName": {k: True for k in hide}, "renameByName": rename or {}}}]
        if sort: tr.append({"id": "sortBy", "options": {"sort": [{"field": sort, "desc": True}]}})
        p["transformations"] = tr
        panels.append(p)
    def logs(self, title, expr, w=12, h=8, desc=""):
        p = base("logs", title, place(w, h, self.c), LOKI, [{"refId": "A", "datasource": LOKI, "expr": expr}], None, desc)
        p["options"] = {"showTime": True, "wrapLogMessage": True, "dedupStrategy": "none", "sortOrder": "Descending", "enableLogDetails": True, "prettifyLogMessage": False}
        panels.append(p)
    def servicemap(self, title, w=12, h=10, desc=""):
        p = base("nodeGraph", title, place(w, h, self.c), TEMPO,
                 [{"refId": "A", "datasource": TEMPO, "queryType": "serviceMap", "serviceMapQuery": "{}"}], None, desc)
        panels.append(p)
    def flame(self, title, w=12, h=10, desc=""):
        p = base("flamegraph", title, place(w, h, self.c), PYRO,
                 [{"refId": "A", "datasource": PYRO, "profileTypeId": "process_cpu:cpu:nanoseconds:cpu:nanoseconds",
                   "labelSelector": "{service_name=\"backstage\"}", "queryType": "profile"}], None, desc)
        panels.append(p)
    def done(self):
        _y[0] += self.c[1] + self.c[2]

# ------------------------------------------------------------------ 1. Adoption
row("Adoption  —  who uses the portal, and what for  (frontend AnalyticsApi → OTLP logs → count connector)")
g = Grid()
g.stat("Active users (1h)", 'count(count by (enduser_id) (increase(backstage_analytics_events_total{enduser_id!="anonymous"}[1h])))', desc="Distinct enduser.id seen in frontend events")
g.stat("Page views (1h)", 'sum(increase(backstage_analytics_events_total{backstage_analytics_action="navigate"}[1h]))', decimals=0)
g.stat("Searches (1h)", 'sum(increase(backstage_search_queries_total[1h]))', decimals=0)
g.stat("Templates run (1h)", 'sum(increase(scaffolder_task_count_total[1h]))', decimals=0, desc="Backstage built-in meter scaffolder.task.count (needs the SDK layer)")
g.stat("Catalog entities", 'sum(catalog_entities_count)', decimals=0, desc="Backstage built-in meter")
g.stat("Hours saved (1h)", 'sum(sum_over_time({service_name="backstage-frontend"} | backstage_analytics_action="create" | unwrap backstage_analytics_value [1h])) / 60', unit="h", decimals=1, desc="Sum of the create event value = template backstage.io/time-saved annotation")
panels[-1]["datasource"] = LOKI; panels[-1]["targets"] = [{"refId": "A", "datasource": LOKI, "expr": panels[-1]["targets"][0]["expr"], "instant": True, "queryType": "instant"}]
g.ts("Plugin usage (frontend events/min)", [('sum by (backstage_plugin) (rate(backstage_analytics_events_total{backstage_analytics_action=~"navigate|click|search|create|discover"}[5m])) * 60', "{{backstage_plugin}}")], w=12, stack=True)
g.bar("Who runs templates (audit events)", 'sum by (backstage_actor) (increase(backstage_audit_events_total{plugin="scaffolder", eventId="task", backstage_action_type="create", status="succeeded"}[24h]))', w=6, legend="{{backstage_actor}}", desc="Backstage auditor service → winston → OTel logs → count connector. No code in Backstage knows this metric exists.")
g.bar("Template popularity", 'sum by (template) (increase(scaffolder_task_count_total[24h]))', w=6, legend="{{template}}")
g.done()

# ------------------------------------------------------------------ 2. Friction
row("Developer friction  —  where people get stuck")
g = Grid()
g.ts("Scaffolder failure rate by template", [('sum by (template) (rate(scaffolder_task_count_total{result="failed"}[10m])) / sum by (template) (rate(scaffolder_task_count_total[10m]))', "{{template}}")], unit="percentunit", maxv=1)
g.ts("Scaffolder p95 duration by template", [('histogram_quantile(0.95, sum by (le, template) (rate(scaffolder_task_duration_seconds_bucket[10m])))', "{{template}}")], unit="s")
g.ts("Slowest template steps (p95)", [('topk(5, histogram_quantile(0.95, sum by (le, template, step) (rate(scaffolder_step_duration_seconds_bucket[10m]))))', "{{template}} / {{step}}")], unit="s")
g.stat("Zero-result searches", 'sum(increase(backstage_search_queries_total{backstage_search_zero_results="true"}[1h])) / sum(increase(backstage_search_queries_total[1h]))', unit="percentunit", thresholds=[{"color": "green", "value": None}, {"color": "orange", "value": 0.2}, {"color": "red", "value": 0.4}], desc="search events whose result count was 0")
g.stat("Ghost entity lookups (1h)", 'sum(increase(backstage_audit_events_total{plugin="catalog", eventId="entity-fetch", status="failed"}[1h]))', decimals=0, thresholds=[{"color": "green", "value": None}, {"color": "orange", "value": 20}], desc="catalog entity-fetch audit events that failed = links to things that no longer exist")
g.stat("TechDocs 404s (1h)", 'sum(increase(traces_span_metrics_calls_total{backstage_plugin="techdocs", http_response_status_code="404"}[1h]))', decimals=0, thresholds=[{"color": "green", "value": None}, {"color": "red", "value": 10}])
g.stat("Failed template runs (1h)", 'sum(increase(scaffolder_task_count_total{result="failed"}[1h]))', decimals=0, thresholds=[{"color": "green", "value": None}, {"color": "red", "value": 1}])
g.ts("4xx / 5xx by plugin (req/s)", [('sum by (backstage_plugin, http_response_status_code) (rate(traces_span_metrics_calls_total{http_response_status_code=~"4..|5.."}[5m]))', "{{backstage_plugin}} {{http_response_status_code}}")], w=8)
g.done()

# ------------------------------------------------------------------ 3. Plugins as products
row("Plugins as products  —  RED per plugin, derived from spans (OBI in layer 0, SDK in layer 1)")
g = Grid()
g.ts("Requests/s by plugin", [('sum by (backstage_plugin) (rate(traces_span_metrics_calls_total{backstage_plugin!=""}[2m]))', "{{backstage_plugin}}")], unit="reqps", stack=True)
g.ts("Error ratio by plugin (5xx)", [('sum by (backstage_plugin) (rate(traces_span_metrics_calls_total{backstage_plugin!="", http_response_status_code=~"5.."}[5m])) / sum by (backstage_plugin) (rate(traces_span_metrics_calls_total{backstage_plugin!=""}[5m]))', "{{backstage_plugin}}")], unit="percentunit")
g.ts("p95 latency by plugin", [('histogram_quantile(0.95, sum by (le, backstage_plugin) (rate(traces_span_metrics_duration_milliseconds_bucket{backstage_plugin!=""}[5m])))', "{{backstage_plugin}}")], unit="ms")
g.table("Slowest routes (p95, 10m)", 'topk(12, histogram_quantile(0.95, sum by (le, backstage_plugin, http_route) (rate(traces_span_metrics_duration_milliseconds_bucket{backstage_plugin!="", http_route!=""}[10m]))))', w=12, unit="ms", rename={"Value": "p95 ms", "backstage_plugin": "plugin", "http_route": "route"}, sort="p95 ms")
g.servicemap("Service graph (Postgres databases are per plugin)", w=12, desc="service_graph connector; each plugin's database shows up as its own node")
g.done()

# ------------------------------------------------------------------ 4. Runtime
row("Runtime  —  from the kernel, zero code: OBI Node.js runtime metrics + eBPF profiles + postgresql receiver")
g = Grid()
g.ts("Event loop utilization", [('max(nodejs_eventloop_utilization_ratio{service_name="backstage"})', "utilization")], unit="percentunit", maxv=1, w=6)
g.ts("Event loop delay p99", [('max(nodejs_eventloop_delay_p99_seconds{service_name="backstage"})', "p99")], unit="s", w=6)
g.ts("GC time by type", [('sum by (v8js_gc_type) (rate(v8js_gc_duration_seconds_sum{service_name="backstage"}[1m]))', "{{v8js_gc_type}}")], unit="percentunit", w=6, stack=True)
g.ts("Heap used by space", [('sum by (v8js_heap_space_name) (v8js_memory_heap_used_bytes{service_name="backstage"})', "{{v8js_heap_space_name}}")], unit="bytes", w=6, stack=True)
g.flame("CPU profile: backstage (eBPF profiler, JS frames)", w=12)
g.ts("Postgres ops/s by plugin database", [('sum by (db_namespace) (rate(db_client_operation_duration_seconds_count{db_namespace!=""}[2m]))', "{{db_namespace}}")], unit="ops", w=6, stack=True)
g.ts("Postgres server: commits vs rollbacks", [('sum(rate(postgresql_commits_total[1m]))', "commits"), ('sum(rate(postgresql_rollbacks_total[1m]))', "rollbacks")], unit="ops", w=6)
g.done()

# ------------------------------------------------------------------ 5. Cost
row("Cost of looking  —  what the pipeline itself costs")
g = Grid()
g.ts("Collector export rate", [('sum(rate(otelcol_exporter_sent_spans[1m]))', "spans/s"), ('sum(rate(otelcol_exporter_sent_log_records[1m]))', "log records/s"), ('sum(rate(otelcol_exporter_sent_metric_points[1m]))', "metric points/s")], w=12, unit="short")
g.logs("Audit trail (who did what)", '{service_name="backstage"} | isAuditEvent="true" | status!="initiated" | line_format "{{.plugin}}.{{.eventId}} {{.status}} actor={{.backstage_actor}} {{.backstage_template}}{{.backstage_query_type}}"', w=12)
g.done()

dash = {
    "uid": "backstage-product", "title": "Backstage as a Product", "tags": ["backstage", "backstagecon"],
    "timezone": "browser", "schemaVersion": 39, "version": 1, "refresh": "10s",
    "time": {"from": "now-30m", "to": "now"}, "editable": True, "graphTooltip": 1,
    "panels": panels, "templating": {"list": []}, "annotations": {"list": []},
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboards", "backstage-product.json")
json.dump(dash, open(out, "w"), indent=1)
print("wrote", out, "panels:", len(panels))
