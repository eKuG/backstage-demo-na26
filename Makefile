# BackstageCon NA 2026 demo. Everything runs on this laptop in Docker Desktop (Linux VM kernel => eBPF works).
LAYER ?= 0
COMPOSE = docker compose -f rig/docker-compose.yaml

.PHONY: build up down reset layer0 layer1 load noload logs ps obi-logs

build:            ## build the Backstage image (node 22)
	cd backstage && . ~/.nvm/nvm.sh && nvm use 22 >/dev/null && yarn tsc && yarn build:backend && yarn build-image

up:               ## start backends + Backstage + OBI (layer 0 by default)
	LAYER=$(LAYER) $(COMPOSE) up -d

down:
	$(COMPOSE) --profile load down -v --remove-orphans

reset: down up    ## clean slate

layer0:           ## Backstage untouched; OBI owns traces/RED/runtime/network
	LAYER=0 OBI_TRACES=on $(COMPOSE) up -d backstage obi otelcol

layer1:           ## one env var: NODE_OPTIONS=--require auto-instrumentations-node/register
	LAYER=1 OBI_TRACES=off $(COMPOSE) up -d backstage obi otelcol

load:             ## synthetic developers (does not touch backstage; keeps whatever layer is running)
	$(COMPOSE) --profile load up -d --no-deps loadgen

noload:
	$(COMPOSE) --profile load stop loadgen

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=50 backstage

obi-logs:
	$(COMPOSE) logs -f --tail=100 obi
