#!/bin/sh
set -eu

KEY=/home/jens/.ssh/id_ed25519
TMUX_DIR=/home/jens/tmux

: "${TTYD_USER:?TTYD_USER is required}"
: "${TTYD_PASSWORD:?TTYD_PASSWORD is required}"

mkdir -p "${TMUX_DIR}"
export TMUX_TMPDIR="${TMUX_DIR}"

i=0
while [ ! -f "${KEY}" ]; do
  i=$((i + 1))
  if [ "${i}" -gt 60 ]; then
    echo "timeout waiting for ${KEY}" >&2
    exit 1
  fi
  sleep 1
done

exec ttyd --port 7681 -W \
  --credential "${TTYD_USER}:${TTYD_PASSWORD}" \
  /usr/local/bin/shell-session.sh
