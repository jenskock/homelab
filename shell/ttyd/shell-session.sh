#!/bin/sh
set -eu

export TMUX_TMPDIR="${TMUX_TMPDIR:-/home/jens/tmux}"
mkdir -p "${TMUX_TMPDIR}"

exec tmux new-session -A -s shell -- ssh \
  -i /home/jens/.ssh/id_ed25519 \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=accept-new \
  -o UserKnownHostsFile=/tmp/known_hosts \
  jens@shell-sshd
