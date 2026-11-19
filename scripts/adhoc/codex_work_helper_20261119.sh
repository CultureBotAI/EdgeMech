#!/bin/bash
# Purpose: invoke the user's pinned work-account wrapper without full shell startup.
# Inputs: wrapper path, pinned native path, then CLI arguments; output: native streams.
# Serves the 2026-11-19 content-review implementation; no scientific-review authority.
set -eu
wrapper=$1
native=$2
shift 2
. "$wrapper"
declare -F codex-work >/dev/null
# #215: fail if wrapper initialization changed executable resolution.
test "$(command -v codex)" = "$native"
codex-work "$@"
