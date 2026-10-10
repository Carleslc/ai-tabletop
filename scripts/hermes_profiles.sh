#!/usr/bin/env bash
# Create the Hermes profiles for the table runner: tabletop-keeper (GM) and tabletop-player.
#
#   scripts/hermes_profiles.sh <worker-url> [gm-repo] [table-repo]
#
# <worker-url>  e.g. https://ai-tabletop-play.<you>.workers.dev
# [gm-repo]     where the GM skills live (default: this repository; use your private
#               copy with the books, e.g. ~/ai-tabletop-keeper)
# [table-repo]  clone of the table repository, for the player skill (default: [gm-repo])
#
# Existing profiles are left alone: SOUL.md and config.yaml are only written to new ones.
# Other names: KEEPER_PROFILE=... PLAYER_PROFILE=... MCP_NAME=... scripts/hermes_profiles.sh ...
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
URL="${1:?usage: $0 <worker-url> [gm-repo] [table-repo]}"; URL="${URL%/}"
GM_REPO="$(cd "${2:-$HERE}" && pwd)"
TABLE_REPO="$(cd "${3:-$GM_REPO}" && pwd)"
HOME_DIR="$HOME/.hermes"  # profiles always live here, whatever HERMES_HOME says
KEEPER="${KEEPER_PROFILE:-tabletop-keeper}"; PLAYER="${PLAYER_PROFILE:-tabletop-player}"
MCP_NAME="${MCP_NAME:-ai-tabletop}"  # the worker's MCP server name, as seats list it in "toolsets"

install() {  # template, profile name, skill, repo with the skill
  local tpl="$1" name="$2" skill="$3" repo="$4" dir="$HOME_DIR/profiles/$2"
  if [ -d "$dir" ]; then echo "$name: exists, skipped"; return; fi
  hermes profile create "$name" --no-skills --no-alias >/dev/null
  cp "$HERE/hermes/$tpl/SOUL.md" "$dir/SOUL.md"
  sed -e "s#{{AI_TABLETOP}}#$HERE#g" -e "s#{{PROFILE}}#$dir#g" -e "s#{{WORKER_URL}}#$URL#g" -e "s#{{MCP_NAME}}#$MCP_NAME#g" \
    "$HERE/hermes/$tpl/config.yaml" > "$dir/config.yaml"
  mkdir -p "$dir/skills/tabletop"
  ln -sfn "$repo/skills/$skill" "$dir/skills/tabletop/$skill"
  echo "$name: created ($skill -> $repo/skills/$skill)"
}

install tabletop-keeper "$KEEPER" coc-kp "$GM_REPO"
install tabletop-player "$PLAYER" coc-player "$TABLE_REPO"
cat <<EOF

Next:
  1. Add the worker's token for the players (not shown on screen):
       read -rs T && echo "TABLETOP_AUTH_TOKEN=\$T" >> "$HOME_DIR/profiles/$PLAYER/.env"
  2. Log in the providers you use, per profile: hermes -p $KEEPER auth add anthropic (and the same for $PLAYER)
  3. Check: hermes -p $PLAYER mcp list
EOF
