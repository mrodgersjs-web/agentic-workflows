#!/bin/bash
# deploy.sh — sync stack configs to rig256gb and compose-up on the offload colima daemon
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
R="ssh -o BatchMode=yes rig256gb"
SOCK="/Users/rig256gb/.colima/offload/docker.sock"
rsync -a --delete --exclude '.env' "$ROOT/deploy/" rig256gb:./agentic-designers/
$R "bash -s" < "$ROOT/scripts/generate-env.sh"
for tool in "$@"; do
  echo "== $tool"
  $R "export PATH=/Users/rig256gb/.docker-side/bin:/opt/homebrew/bin:/usr/local/bin:/Users/rig256gb/.docker/cli-plugins:/usr/bin:/bin DOCKER_CONFIG=/Users/rig256gb/.docker-side; docker -H unix://$SOCK compose -p ad-$tool -f ~/agentic-designers/$tool/docker-compose.yml --env-file ~/agentic-designers/$tool/.env up -d" 2>&1 | tail -3
done
