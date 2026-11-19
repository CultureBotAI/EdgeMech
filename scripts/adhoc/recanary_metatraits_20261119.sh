#!/bin/bash
# Purpose: repeat bounded owner replays after #221; date: 2026-11-19.
# Inputs: plan|replay|verify, first43|first28, private attempt label.
# Outputs: exclusive source receipt/readback beneath this clone's .temp/.
# Both cases use the same clean shell environment and retained owner Python.
set -euo pipefail
umask 077

if [[ $# != 3 ]]; then
  echo 'usage: recanary_metatraits_20261119.sh MODE CASE ATTEMPT' >&2
  exit 2
fi
case "$1" in plan|replay|verify) ;; *) exit 2 ;; esac
case "$2" in
  first43) packet=first-43 ;;
  first28) packet=first-28 ;;
  *) exit 2 ;;
esac
[[ "$3" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || exit 2
root=$(cd "$(dirname "$0")/../.." && pwd -P)
output_parent="$root/.temp/source-recanary-221-20261119"
mkdir -p "$output_parent"
chmod 700 "$output_parent"
owner_python=/Users/marcin/agent-work/EdgeMech/pr1871-cleanup-20261119/preserved-worktree-artifacts/payload/.venv310/bin/python
owner=/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe
packets=/Users/marcin/agent-work/EdgeMech/m5-calibration-round03-20261116/.temp/edge-calibration-20261115
cd "$root"
exec /usr/bin/env -i HOME=/Users/marcin LANG=en_US.UTF-8 \
  PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$owner_python" -B scripts/adhoc/replay_metatraits_discrete_20261119.py \
  "$1" --case "$2" --kg "$owner" --original "$packets/$packet" \
  --output "$output_parent/$3"
