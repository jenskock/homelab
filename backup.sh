#!/bin/bash
set -euo pipefail

NAS_HOST="192.168.188.112"
NAS_EXPORT="/volume1/homes"
MOUNT_POINT="/mnt/synology_backup"
BACKUP_ROOT="${MOUNT_POINT}/jens/Backup/jesktop.local"
KEEP_COUNT=7
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
EXCLUDE_PATTERN="*/diagnostic.data/metrics*"

OPT_SOURCES=(
  /opt/portainer
  /opt/cloudflared
  /opt/bitwarden
  /opt/n8n
  /opt/open-webui
  /opt/paperless
  /opt/kavita
)

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo)."
  exit 1
fi

if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
  echo "Mounting NAS..."
  mkdir -p "$MOUNT_POINT"
  mount -t nfs "${NAS_HOST}:${NAS_EXPORT}" "$MOUNT_POINT"
fi

if [ ! -d "$BACKUP_ROOT" ]; then
  echo "Backup root '${BACKUP_ROOT}' does not exist."
  exit 1
fi

mkdir -p "$BACKUP_DIR"
echo "Starting backup: ${BACKUP_DIR}"

for src in "${OPT_SOURCES[@]}"; do
  name="$(basename "$src")"
  if [ ! -d "$src" ]; then
    echo "Skip ${name}: not found"
    continue
  fi
  echo "Backing up ${src}"
  tar --exclude="$EXCLUDE_PATTERN" -czf "${BACKUP_DIR}/${name}.tar.gz" -C "$(dirname "$src")" "$name"
done

count="$(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
if [ "$count" -gt "$KEEP_COUNT" ]; then
  find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d \
    | sort \
    | head -n "$((count - KEEP_COUNT))" \
    | while read -r old; do
        echo "Removing old backup ${old}"
        rm -rf "$old"
      done
fi

echo "Backup finished."
du -sh "$BACKUP_DIR"
