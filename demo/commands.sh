# Pre-typed terminal commands for the demo. Keep this file open; copy one line at a time.
cd ~/Documents/backstagecon-2026   # or: git clone https://github.com/eKuG/backstage-demo-na26

# --- what OBI did to Backstage (Beat A) ---
docker logs obi 2>&1 | grep -E 'type=nodejs|Script successfully injected'

# --- what Backstage knows about OTel: nothing (Beat A) ---
docker inspect backstage --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E '^(NODE_OPTIONS|OTEL_)'

# --- the env file behind layer 1 (Beat B) ---
cat rig/layers/1.env

# --- optional live flip (only if ahead of time; ~3 s to ready, ~10 s to first meters) ---
make layer1      # SDK on
make layer0      # SDK off, OBI owns everything again
until curl -fsS -o /dev/null localhost:7007/.backstage/health/v1/readiness; do sleep 1; done; echo READY

# --- the three Collector derivations (Beat C): open in editor, not terminal ---
code rig/collector/config.yaml                                   # transform/plugin (line ~40), count (line ~80)
code backstage/packages/app/src/modules/analytics/OtlpAnalytics.ts

# --- synthetic developers on/off ---
make load
make noload
