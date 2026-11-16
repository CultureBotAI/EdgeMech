#!/usr/bin/env bash
# Purpose: stage retained EdgeMech inputs on M5 without replacing existing evidence.
# Inputs: canonical private staging, retained-100 archive and KG v3 evidence.
# Outputs: same-path M5 copies and private transfer/checksum logs in this worktree.
# Serves: user-authorized M5 work and review findings #139-141, 2026-11-16.
set -euo pipefail

mode=${1:?Use --plan, --canary, --copy or --verify}
case "$mode" in --plan|--canary|--copy|--verify) ;; *) exit 2 ;; esac
root=$(cd "$(dirname "$0")/../.." && pwd)
host=marcins-MacBook-Pro-3.local
edge=/Users/marcin/Documents/VIMSS/ontology/Mechs/EdgeMech
archive=/Users/marcin/agent-work/EdgeMech/edge-sample-review-20261112-data
retained=/Users/marcin/agent-work/EdgeMech/retained-pr135-pr1867-20261116
logroot="$root/.temp/m5-input-transfer-20261116-v3"
canary_dir="$archive/sample/private-provenance"
canary_src="$archive/sample/private-provenance/canary.jsonl"
canary_sha=757e9c7f48ba621369c5065167b5fcb2892dcdd5f0a57fe3950d7edacb896ba9
paths=(
  "$archive"
  "$edge/.temp/edge-calibration-20261115"
  "$edge/.temp/edge-calibration-authorities-20261115"
  "$edge/.temp/occurrence-canary-edge47-125-fixed-20261115"
  "$edge/.temp/identity130-review-v2-20261115"
  "$edge/.temp/identity130/authorities"
  "$retained/kg-candidate/data/validation-bactotraits-130/baseline-v3-20261116"
  "$retained/kg-candidate/data/validation-bactotraits-130/candidate-v3-20261116"
)
ssh_args=(-o BatchMode=yes -o ConnectTimeout=15)

verify_canary() {
  local actual
  actual=$(ssh "${ssh_args[@]}" "$host" "shasum -a 256 '$canary_dir/canary.jsonl'")
  test "${actual%% *}" = "$canary_sha"
}

for input in "${paths[@]}"; do
  test -d "$input"
done
test "$(shasum -a 256 "$canary_src" | cut -d ' ' -f 1)" = "$canary_sha"

if [ "$mode" = --plan ]; then
  printf 'Destination: %s; existing files are never overwritten.\n' "$host"
  du -sk "${paths[@]}"
  ssh "${ssh_args[@]}" "$host" "df -k '/Users/marcin'; test -d '$edge/.git'"
  exit 0
fi

umask 077
mkdir -p "$logroot"
if [ "$mode" = --canary ]; then
  ssh "${ssh_args[@]}" "$host" "test ! -e '$canary_dir/canary.jsonl' && test ! -L '$canary_dir/canary.jsonl' && umask 077 && mkdir -p '$canary_dir'"
  rsync -a --chmod=Du=rwx,Dgo=,Fu=rw,Fgo= --ignore-existing \
    -e 'ssh -o BatchMode=yes -o ConnectTimeout=15' \
    "$canary_src" "$host:$canary_dir/" > "$logroot/canary-transfer.log"
  verify_canary
  printf '%s  %s\n' "$canary_sha" "$canary_dir/canary.jsonl" > "$logroot/canary.sha256"
  printf 'One real file transferred and independently hash-verified on M5.\n'
  exit 0
fi

test -s "$logroot/canary.sha256"
verify_canary
if [ "$mode" = --copy ]; then
  for input in "${paths[@]}"; do
    ssh "${ssh_args[@]}" "$host" "umask 077; mkdir -p '$input' && chmod 700 '$input'"
    rsync -a --chmod=Du=rwx,Dgo=,Fu=rw,Fgo= --ignore-existing \
      -e 'ssh -o BatchMode=yes -o ConnectTimeout=15' \
      "$input/" "$host:$input/" >> "$logroot/transfer.log"
  done
fi

# Content checksum dry-run detects missing or different remote source files.
# Remote-only files are retained; no --delete or overwriting sync is permitted.
verification="$logroot/verification-$mode.log"
: > "$verification"
for input in "${paths[@]}"; do
  rsync -rcni --out-format='%i %n' -e 'ssh -o BatchMode=yes -o ConnectTimeout=15' \
    "$input/" "$host:$input/" >> "$verification"
done
if [ -s "$verification" ]; then
  printf 'Missing or differing files remain; inspect %s. Nothing was overwritten.\n' "$verification" >&2
  exit 1
fi
printf 'All selected source files match their M5 copies by checksum; original evidence retained.\n'
