# Treating Backstage Like a Product: Observability with OpenTelemetry

Demo rig for the BackstageCon North America 2026 talk (Salt Lake City, Nov 9, 2026). Slides: [`deck/backstagecon-na-2026.pdf`](deck/backstagecon-na-2026.pdf).

A stock Backstage 1.56 observed in four layers, with **product metrics** (adoption, friction, reliability per plugin) derived in the OpenTelemetry Collector. Backstage itself emits none of them.

| Layer | How | What only it gives |
|---|---|---|
| 0 · Kernel | [OBI](https://github.com/open-telemetry/opentelemetry-ebpf-instrumentation) v1.0.0 (eBPF), one privileged container, zero code | Traces incl. Postgres per table, RED per route, Node event loop / GC / heap, network flows |
| 1 · Runtime | one env var: `NODE_OPTIONS=--require @opentelemetry/auto-instrumentations-node/register` | In-process spans, winston logs with trace ids, Backstage's own meters (`scaffolder.task.*`, `catalog_*`) |
| 2 · Product | Backstage auditor service (`backend.auditor.severityLogLevelMappings.low: info`) | Who did what, did it work: template runs by actor, ghost entity lookups |
| 3 · User | a 90-line `AnalyticsApi` module that POSTs OTLP/JSON from the browser | navigate, click, search (result count), create (time saved) |

The Collector (`rig/collector/config.yaml`) turns all of it into product metrics: an OTTL regex gives every span a `backstage.plugin` dimension, `span_metrics` produces RED per plugin, and the `count` connector turns audit and frontend events into counters. Everything lands in Prometheus, Tempo, Loki and Pyroscope, and a 36-panel Grafana dashboard reads it.

## Run it

Needs Docker Desktop (macOS: its Linux VM kernel is what eBPF attaches to) or any Linux box with Docker, plus Node 22 and Yarn to build the Backstage image once.

```sh
make build     # once: builds the Backstage image (node 22)
make up        # Postgres, Backstage, OBI, eBPF profiler, Collector, Prometheus, Tempo, Loki, Pyroscope, Grafana
make load      # synthetic developers, ~8 rps (catalog reads, searches, templates, 404s)
make layer1    # flip the SDK layer on; make layer0 flips it off
make down      # everything, volumes included
```

| URL | What |
|---|---|
| http://localhost:7007 | Backstage (sign in as Guest) |
| http://localhost:3300/d/backstage-product?kiosk | the dashboard |
| http://localhost:3300/explore | Tempo / Loki / Pyroscope |
| http://localhost:9090 | Prometheus |

Three templates tell the friction story: `paved-road-service` (always succeeds, declares 4 h saved), the stock `example-nodejs-template` (fails at `publish:github` without a token), `slow-data-pipeline` (8 s, the p95 outlier).

## Layout

- `rig/docker-compose.yaml`, `rig/layers/*.env`: the stack and the layer switches
- `rig/collector/config.yaml`: the product-metric derivations (the interesting file)
- `rig/grafana/gen_dashboard.py` → `rig/grafana/dashboards/backstage-product.json`
- `backstage/`: a fresh `create-app` 1.56 plus `packages/app/src/modules/analytics/` (AnalyticsApi → OTLP) and `examples/templates/`
- `evidence/`: screenshots from the rig; `research/NOTES.md`: facts and sources behind the talk
- `demo/`: bookmarks and pre-typed commands used on stage

## Things that bit us

- OBI exports traces even when only a metrics endpoint is configured; the Collector drops OBI's copy in layer 1 (`OBI_TRACES=off`) so RED is not double counted.
- The OTel winston instrumentation only ships log records when `@opentelemetry/winston-transport` is installed.
- Audit events default to severity `low` = debug, which the logger drops; map `low` to `info`.
- OBI's header propagation is disabled on the Docker Desktop 7.0 kernel; async context still works, so traces nest fine.
- `actor.actorId` is a user ref: hash it before it becomes a Prometheus label.
