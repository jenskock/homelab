#!/bin/sh
set -eu

STAGING_ROOT="${STAGING_ROOT:-/data}"
OUTBOX="${STAGING_ROOT}/outbox"
DONE="${STAGING_ROOT}/done"
FAILED="${STAGING_ROOT}/failed"
POLL_SECONDS="${POLL_SECONDS:-2}"
MIN_AGE_SECONDS="${MIN_AGE_SECONDS:-1}"

mkdir -p "$OUTBOX" "$DONE" "$FAILED"

log() {
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"
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

process_file() {
  file="$1"
  base=$(basename "$file")
  meta="${file}.meta.json"
  errfile="${FAILED}/${base}.err"
  upload_path="$file"

  if [ ! -f "$meta" ]; then
    log "skip ${base}: waiting for meta"
    return 0
  fi

  now=$(date +%s)
  mtime=$(stat -c %Y "$file")
  age=$((now - mtime))
  if [ "$age" -lt "$MIN_AGE_SECONDS" ]; then
    log "skip ${base}: too new (${age}s)"
    return 0
  fi

  folder=$(sed -n 's/.*"folder"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$meta" | head -n1)
  name=$(sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$meta" | head -n1)

  [ -n "$folder" ] || folder="/Inbox"
  folder=$(printf '%s' "$folder" | sed 's:/*$::')
  case "$folder" in
    /*) ;;
    *) folder="/$folder" ;;
  esac
  [ -n "$name" ] || name="$base"
  name=$(basename "$name")

  if [ "$name" != "$base" ]; then
    upload_path="/tmp/${name}"
    cp -f "$file" "$upload_path"
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

  if [ "$upload_path" != "$file" ]; then
    rm -f "$upload_path"
  fi

  if [ "$put_rc" -eq 0 ]; then
    log "OK ${base}"
    mv -f "$file" "$DONE/"
    mv -f "$meta" "$DONE/"
    rm -f "$errfile"
  else
    log "FAIL ${base}: ${out}"
    echo "$out" >"$errfile"
    mv -f "$file" "$FAILED/"
    mv -f "$meta" "$FAILED/"
  fi
}

log "rmapi watch started (outbox=${OUTBOX})"
while true; do
  for file in "$OUTBOX"/*.pdf "$OUTBOX"/*.rmdoc "$OUTBOX"/*.rmn "$OUTBOX"/*.zip; do
    [ -f "$file" ] || continue
    process_file "$file" || log "error processing ${file}"
  done
  sleep "$POLL_SECONDS"
done
