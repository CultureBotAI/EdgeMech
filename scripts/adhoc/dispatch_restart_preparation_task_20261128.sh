#!/bin/bash
# Purpose: one authorized task to the existing idle worker; never launch a client.
# Inputs: paste/submit mode, tmux binary/socket, exact pane/client bindings,
# caller-reviewed screen SHA256, prompt path/SHA256 and a unique buffer name.
# Outputs: one paste OR one explicitly client-bound Enter; never both together.
# Caller retains unique attempt receipts and independently verifies acceptance.
# Caller preflights exact native thread/process/cwd/model and no human prompt.
# Submit requires a new inspected composer capture; do not repeat a missing Enter
# by pasting the task again. Original acbe985b execution/acceptance stay private.
# Outputs: tmux input
# and native stdout status, retained privately with the invocation. UTC2026-11-28.
# Issues228/220: prospective dispatch source, not a historical helper replay.
# Caller must inspect an empty composer for paste, or the exact draft for submit.
# A changed screen or identity refuses input. A partial paste is preserved on error.
set -euo pipefail
test "$#" -eq 11
operation=$1
tmux_bin=$2
tmux_socket=$3
worker_pane=$4
expected_binding=$5
control_client=$6
expected_client_binding=$7
expected_screen_sha=$8
prompt_path=$9
expected_prompt_sha=${10}
buffer_name=${11}
case "$operation" in paste|submit) ;; *) exit 2 ;; esac
case "$expected_client_binding" in *'|0') ;; *) exit 2 ;; esac
test "${expected_client_binding%%|*}" = "$control_client"
test -f "$prompt_path"
test ! -L "$prompt_path"
test -s "$prompt_path"
test "$(/usr/bin/shasum -a 256 "$prompt_path" | /usr/bin/awk '{print $1}')" = "$expected_prompt_sha"
check_state() {
    # display-message -c may still format another ambient client with -p/-t.
    # Match the actual requested client directly in the complete live inventory.
    client_inventory=$("$tmux_bin" -N -S "$tmux_socket" list-clients -F '#{client_name}|#{client_pid}|#{client_tty}|#{client_readonly}')
    /usr/bin/grep -Fxq -- "$expected_client_binding" <<< "$client_inventory"
    observed_pane=$("$tmux_bin" -N -S "$tmux_socket" display-message -p -t "$worker_pane" '#{session_name}|#{pane_id}|#{pane_pid}|#{pane_tty}|#{pane_current_path}')
    test "$observed_pane" = "$expected_binding"
    observed_screen_sha=$("$tmux_bin" -N -S "$tmux_socket" capture-pane -p -t "$worker_pane" -S -28 | /usr/bin/shasum -a 256 | /usr/bin/awk '{print $1}')
    test "$observed_screen_sha" = "$expected_screen_sha"
}
check_state
if test "$operation" = paste; then
    buffer_inventory=$("$tmux_bin" -N -S "$tmux_socket" list-buffers -F '#{buffer_name}')
    if /usr/bin/grep -Fxq -- "$buffer_name" <<< "$buffer_inventory"; then
        exit 2
    fi
    "$tmux_bin" -N -S "$tmux_socket" load-buffer -b "$buffer_name" "$prompt_path"
    trap '"$tmux_bin" -N -S "$tmux_socket" delete-buffer -b "$buffer_name" 2>/dev/null || true' EXIT
    check_state
    "$tmux_bin" -N -S "$tmux_socket" paste-buffer -p -d -b "$buffer_name" -t "$worker_pane"
    /bin/date -u '+paste_attempted_at_utc=%Y-%m-%dT%H:%M:%SZ'
else
    check_state
    "$tmux_bin" -N -S "$tmux_socket" send-keys -c "$control_client" -t "$worker_pane" Enter
    /bin/date -u '+submit_attempted_at_utc=%Y-%m-%dT%H:%M:%SZ'
fi
