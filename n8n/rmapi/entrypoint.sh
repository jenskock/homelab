#!/bin/sh
set -eu

STAGING_ROOT="${STAGING_ROOT:-/data}"
OUTBOX="${STAGING_ROOT}/outbox"
DONE="${STAGING_ROOT}/done"
FAILED="${STAGING_ROOT}/failed"
POLL_SECONDS="${POLL_SECONDS:-2}"
MIN_AGE_SECONDS="${MIN_AGE_SECONDS:-1}"
FOLDER_RE='^(/[A-Za-z0-9._-]+)+$'

mkdir -p "$OUTBOX" "$DONE" "$FAILED"

log() {
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"
}

validate_folder() {
  echo "$1" | grep -Eq "$FOLDER_RE"
}

ensure_remote_folder() {
  folder="$1"
  accumulated=""
  old_ifs=$IFS
  IFS=/
  set -- $folder
  IFS=$old_ifs
  for segment in "$@"; do
    [ -z "$segment" ] && continue
    accumulated="${accumulated}/${segment}"
    rel="${accumulated#/}"
    if ! rmapi ls "$accumulated" >/dev/null 2>&1; then
      log "creating remote folder ${accumulated}"
      rmapi mkdir "$rel" || rmapi ls "$accumulated" >/dev/null 2>&1 || return 1
    fi
  done
}

process_pdf() {
  pdf="$1"
  base=$(basename "$pdf")
  meta="${pdf}.meta.json"
  errfile="${FAILED}/${base}.err"
  upload_path="$pdf"

  if [ ! -f "$meta" ]; then
    log "skip ${base}: waiting for meta"
    return 0
  fi

  now=$(date +%s)
  mtime=$(stat -c %Y "$pdf")
  age=$((now - mtime))
  if [ "$age" -lt "$MIN_AGE_SECONDS" ]; then
    log "skip ${base}: too new (${age}s)"
    return 0
  fi

  folder=$(sed -n 's/.*"folder"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$meta" | head -n1)
  name=$(sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$meta" | head -n1)

  [ -n "$folder" ] || folder="/Inbox"
  [ -n "$name" ] || name="$base"
  name=$(basename "$name")

  if ! validate_folder "$folder"; then
    msg="invalid folder in meta: ${folder}"
    log "FAIL ${base}: ${msg}"
    echo "$msg" >"$errfile"
    mv -f "$pdf" "$FAILED/"
    mv -f "$meta" "$FAILED/"
    return 0
  fi

  if [ "$name" != "$base" ]; then
    upload_path="/tmp/${name}"
    cp -f "$pdf" "$upload_path"
  fi

  log "upload ${base} as ${name} -> ${folder}"
  set +e
  ensure_remote_folder "$folder"
  mkdir_rc=$?
  if [ "$mkdir_rc" -eq 0 ]; then
    out=$(rmapi put --force -- "$upload_path" "$folder" 2>&1)
    put_rc=$?
  else
    out="failed to ensure remote folder ${folder}"
    put_rc=1
  fi
  set -e

  if [ "$upload_path" != "$pdf" ]; then
    rm -f "$upload_path"
  fi

  if [ "$put_rc" -eq 0 ]; then
    log "OK ${base}"
    mv -f "$pdf" "$DONE/"
    mv -f "$meta" "$DONE/"
    rm -f "$errfile"
  else
    log "FAIL ${base}: ${out}"
    echo "$out" >"$errfile"
    mv -f "$pdf" "$FAILED/"
    mv -f "$meta" "$FAILED/"
  fi
}

log "rmapi watch started (outbox=${OUTBOX})"
while true; do
  for pdf in "$OUTBOX"/*.pdf; do
    [ -f "$pdf" ] || continue
    process_pdf "$pdf" || log "error processing ${pdf}"
  done
  sleep "$POLL_SECONDS"
done
