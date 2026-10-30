#!/bin/bash
# generate-env.sh — create .env for each agentic-designers stack (idempotent; secrets only on rig256gb)
set -euo pipefail
D=${1:-$HOME/agentic-designers}
mkdir -p "$D"
AD_TAILNET_IP=${AD_TAILNET_IP:-$RIG_HOST}
rand() { openssl rand -hex 24; }

mk() { # tool, body-lines...
  local tool=$1; shift
  local f="$D/$tool/.env"
  [ -f "$f" ] && { echo "keep $f"; return; }
  mkdir -p "$D/$tool"
  { for kv in "$@"; do echo "$kv"; done; } > "$f"
  chmod 600 "$f"
  echo "created $f"
}

N8N_PASSWORD=$(rand | head -c 16)
mk n8n \
  "N8N_VERSION=3.0.1" \
  "N8N_PORT=5678" \
  "AD_TAILNET_IP=$AD_TAILNET_IP" \
  "N8N_ENCRYPTION_KEY=$(openssl rand -hex 16)" \
  "AD_N8N_OWNER_EMAIL=jake@rig.local" \
  "AD_N8N_OWNER_PASSWORD=$N8N_PASSWORD" \
  "AD_N8N_OWNER_FIRST=Jake" \
  "AD_N8N_OWNER_LAST=PAI"

FLOWISE_PASSWORD=$(rand | head -c 16)
mk flowise \
  "FLOWISE_VERSION=3.1.4" \
  "FLOWISE_PORT=3110" \
  "AD_TAILNET_IP=$AD_TAILNET_IP" \
  "FLOWISE_USERNAME=admin" \
  "FLOWISE_PASSWORD=$FLOWISE_PASSWORD"

TRIGGER_PG=$(rand | head -c 16)
mk trigger \
  "TRIGGER_IMAGE_TAG=v4.6.3" \
  "WEBAPP_PUBLISH_IP=127.0.0.1" \
  "AD_TAILNET_IP=$AD_TAILNET_IP" \
  "POSTGRES_PASSWORD=$TRIGGER_PG" \
  "SESSION_SECRET=$(rand)" "MAGIC_LINK_SECRET=$(rand)" "ENCRYPTION_KEY=$(rand)" \
  "PROVIDER_SECRET=$(rand)" "COORDINATOR_SECRET=$(rand)" "MANAGED_WORKER_SECRET=$(rand)" \
  "CLICKHOUSE_PASSWORD=$(rand | head -c 12)" \
  "OBJECT_STORE_ACCESS_KEY_ID=agentic" \
  "OBJECT_STORE_SECRET_ACCESS_KEY=$(rand)" \
  "MINIO_ROOT_USER=agentic" \
  "MINIO_ROOT_PASSWORD=$TRIGGER_PG" \
  "NODE_MAX_OLD_SPACE_SIZE=1024" \
  "APP_ORIGIN=http://$AD_TAILNET_IP:8030" "LOGIN_ORIGIN=http://$AD_TAILNET_IP:8030" "API_ORIGIN=http://$AD_TAILNET_IP:8030" \
  "DOCKER_REGISTRY_URL=registry:5000" "DOCKER_REGISTRY_NAMESPACE=trigger" \
  "OBJECT_STORE_BASE_URL=http://minio:9000"

mk langgraph \
  "LANGGRAPH_VERSION=0.7.27" \
  "AD_TAILNET_IP=$AD_TAILNET_IP" \
  "LG_PORT=2100" \
  "STUDIO_PORT=2101"

mk crewai \
  "AD_TAILNET_IP=$AD_TAILNET_IP" \
  "CREWAI_PORT=8321" \
  "AD_CREWAI_TOKEN=$(rand)"
