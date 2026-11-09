#!/bin/sh
# Synthetic developers. Weighted mix of the things people actually do in a portal,
# including the things that go wrong (ghost entities, zero-result searches, a template with no GitHub token).
set -u
H="Authorization: Bearer ${TOKEN}"
BASE="${BASE:-http://backstage:7007}"
RPS="${RPS:-5}"
SLEEP=$(awk -v r="$RPS" 'BEGIN{printf "%.3f", 1/r}')
NAMES="example-website example-grpc-api artist-lookup"
i=0
until curl -fsS -o /dev/null "$BASE/.backstage/health/v1/readiness"; do sleep 2; done
echo "backstage ready, generating ~${RPS} rps"
while true; do
  i=$((i+1))
  r=$(awk 'BEGIN{srand(); print int(rand()*100)}')
  if [ "$r" -lt 35 ]; then
    curl -s -o /dev/null -H "$H" "$BASE/api/catalog/entities?filter=kind=component&limit=20"
  elif [ "$r" -lt 50 ]; then
    curl -s -o /dev/null -H "$H" "$BASE/api/catalog/entities/by-name/component/default/example-website"
  elif [ "$r" -lt 55 ]; then
    curl -s -o /dev/null -H "$H" "$BASE/api/catalog/entities/by-name/component/default/ghost-service-$((i%7))"   # 404s
  elif [ "$r" -lt 70 ]; then
    term=$( [ $((i%4)) -eq 0 ] && echo "zzqx-nothing" || echo "example" )
    curl -s -o /dev/null -H "$H" "$BASE/api/search/query?term=$term&types[0]=software-catalog"
  elif [ "$r" -lt 78 ]; then
    curl -s -o /dev/null -H "$H" "$BASE/api/techdocs/static/docs/default/component/example-website/index.html"  # no docs built -> 404
  elif [ "$r" -lt 90 ]; then
    curl -s -o /dev/null "$BASE/"
    curl -s -o /dev/null "$BASE/catalog"
  elif [ "$r" -lt 96 ]; then
    curl -s -o /dev/null -H "$H" -H 'content-type: application/json' -X POST "$BASE/api/scaffolder/v2/tasks" \
      -d "{\"templateRef\":\"template:default/paved-road-service\",\"values\":{\"name\":\"svc-$i\"}}"
  elif [ "$r" -lt 98 ]; then
    curl -s -o /dev/null -H "$H" -H 'content-type: application/json' -X POST "$BASE/api/scaffolder/v2/tasks" \
      -d "{\"templateRef\":\"template:default/example-nodejs-template\",\"values\":{\"name\":\"svc-$i\",\"repoUrl\":\"github.com?owner=example&repo=svc-$i\"}}"
  else
    curl -s -o /dev/null -H "$H" -H 'content-type: application/json' -X POST "$BASE/api/scaffolder/v2/tasks" \
      -d "{\"templateRef\":\"template:default/slow-data-pipeline\",\"values\":{\"name\":\"pipe-$i\"}}"
  fi
  sleep "$SLEEP"
done
