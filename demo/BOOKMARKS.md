# Demo tabs, in order (Chrome; open all before the talk, verified 2026-11-08)

## 1 · Grafana dashboard, kiosk, last hour
http://localhost:3300/d/backstage-product?kiosk&from=now-1h&to=now&refresh=10s

## 2 · Backstage (sign in as Guest once)
http://localhost:7007/

## 3 · Tempo: layer-0 (OBI) scaffolder traces, last 3 h
http://localhost:3300/explore?schemaVersion=1&orgId=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22tempo%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22datasource%22%3A%7B%22type%22%3A%22tempo%22%2C%22uid%22%3A%22tempo%22%7D%2C%22queryType%22%3A%22traceql%22%2C%22query%22%3A%22%7B%20resource.service.name%3D%5C%22backstage%5C%22%20%26%26%20span.http.route%3D%5C%22/api/scaffolder/v2/tasks%5C%22%20%26%26%20resource.telemetry.distro.name%3D%5C%22opentelemetry-ebpf-instrumentation%5C%22%20%7D%22%2C%22limit%22%3A20%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-3h%22%2C%22to%22%3A%22now%22%7D%7D%7D

## 4 · Tempo: layer-1 (SDK) scaffolder traces
http://localhost:3300/explore?schemaVersion=1&orgId=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22tempo%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22datasource%22%3A%7B%22type%22%3A%22tempo%22%2C%22uid%22%3A%22tempo%22%7D%2C%22queryType%22%3A%22traceql%22%2C%22query%22%3A%22%7B%20resource.service.name%3D%5C%22backstage%5C%22%20%26%26%20resource.telemetry.sdk.version%3D%5C%223.0.0%5C%22%20%26%26%20kind%3Dserver%20%26%26%20span.http.route%3D%5C%22/api/scaffolder/v2/tasks%5C%22%20%7D%22%2C%22limit%22%3A20%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-1h%22%2C%22to%22%3A%22now%22%7D%7D%7D

## 5 · Loki: audit trail, scaffolder
http://localhost:3300/explore?schemaVersion=1&orgId=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22loki%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22datasource%22%3A%7B%22type%22%3A%22loki%22%2C%22uid%22%3A%22loki%22%7D%2C%22expr%22%3A%22%7Bservice_name%3D%5C%22backstage%5C%22%7D%20%7C%20isAuditEvent%3D%5C%22true%5C%22%20%7C%20plugin%3D%5C%22scaffolder%5C%22%20%7C%20status%21%3D%5C%22initiated%5C%22%20%7C%20line_format%20%5C%22%7B%7B.plugin%7D%7D.%7B%7B.eventId%7D%7D%20%7B%7B.status%7D%7D%20actor%3D%7B%7B.backstage_actor%7D%7D%20%7B%7B.backstage_template%7D%7D%5C%22%22%2C%22queryType%22%3A%22range%22%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-1h%22%2C%22to%22%3A%22now%22%7D%7D%7D

## 6 · Loki: a backend log line with trace_id
http://localhost:3300/explore?schemaVersion=1&orgId=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22loki%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22datasource%22%3A%7B%22type%22%3A%22loki%22%2C%22uid%22%3A%22loki%22%7D%2C%22expr%22%3A%22%7Bservice_name%3D%5C%22backstage%5C%22%7D%20%7C%20trace_id%21%3D%5C%22%5C%22%20%7C%3D%20%5C%22GET%20/api/catalog%5C%22%22%2C%22queryType%22%3A%22range%22%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-1h%22%2C%22to%22%3A%22now%22%7D%7D%7D

## 7 · Loki: frontend create events (hours saved)
http://localhost:3300/explore?schemaVersion=1&orgId=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22loki%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22datasource%22%3A%7B%22type%22%3A%22loki%22%2C%22uid%22%3A%22loki%22%7D%2C%22expr%22%3A%22%7Bservice_name%3D%5C%22backstage-frontend%5C%22%7D%20%7C%20backstage_analytics_action%3D%5C%22create%5C%22%22%2C%22queryType%22%3A%22range%22%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-1h%22%2C%22to%22%3A%22now%22%7D%7D%7D

## 8 · Pyroscope flame graph via Grafana Explore
http://localhost:3300/explore?schemaVersion=1&orgId=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22pyroscope%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22datasource%22%3A%7B%22type%22%3A%22grafana-pyroscope-datasource%22%2C%22uid%22%3A%22pyroscope%22%7D%2C%22profileTypeId%22%3A%22process_cpu%3Acpu%3Ananoseconds%3Acpu%3Ananoseconds%22%2C%22labelSelector%22%3A%22%7Bservice_name%3D%5C%22backstage%5C%22%7D%22%2C%22queryType%22%3A%22profile%22%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-30m%22%2C%22to%22%3A%22now%22%7D%7D%7D

