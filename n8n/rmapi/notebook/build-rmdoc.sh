#!/bin/sh
# Build a native reMarkable .rmdoc (zip) with blank templated pages.
# Usage:
#   build-rmdoc.sh <visibleName> <output.rmdoc> [pages] [template]
# Defaults: pages=5, template="P Lines medium"
set -eu

NAME="${1:?visible name required}"
OUTPUT="${2:?output .rmdoc path required}"
PAGES="${3:-5}"
TEMPLATE="${4:-P Lines medium}"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
STENCIL="${STENCIL:-$SCRIPT_DIR/blank-page.rm}"
BASE_CONTENT="${BASE_CONTENT:-$SCRIPT_DIR/base.content.json}"
STENCIL_AUTHOR_UUID_OFFSET=58

for dep in jq zip; do
  command -v "$dep" >/dev/null 2>&1 || {
    echo "ERROR: missing dependency: $dep" >&2
    exit 1
  }
done

[ -f "$STENCIL" ] || {
  echo "ERROR: stencil not found: $STENCIL" >&2
  exit 1
}
[ -f "$BASE_CONTENT" ] || {
  echo "ERROR: base content not found: $BASE_CONTENT" >&2
  exit 1
}

case "$PAGES" in
  '' | *[!0-9]* | 0)
    echo "ERROR: pages must be a positive integer" >&2
    exit 1
    ;;
esac

gen_uuid() {
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen | tr 'A-Z' 'a-z'
  else
    cat /proc/sys/kernel/random/uuid
  fi
}

ALPHA='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
idx_key() {
  num=$((2330 + $1 - 1))
  echo "${ALPHA:$((num / 62)):1}${ALPHA:$((num % 62)):1}"
}

patch_stencil_uuid() {
  src="$1"
  out="$2"
  uuid_hex=$(printf '%s' "$AUTHOR_UUID" | tr -d '-')
  escaped=$(printf '%s' "$uuid_hex" | sed 's/../\\x&/g')
  cp -f "$src" "$out"
  printf '%b' "$escaped" |
    dd of="$out" bs=1 seek="$STENCIL_AUTHOR_UUID_OFFSET" count=16 \
      conv=notrunc status=none
}

AUTHOR_UUID=$(gen_uuid)
DOCID=$(gen_uuid)
CREATED_TIME_MS=$(date +%s)000
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/$DOCID"

pages='[]'
i=1
while [ "$i" -le "$PAGES" ]; do
  pid=$(gen_uuid)
  patch_stencil_uuid "$STENCIL" "$WORK/$DOCID/$pid.rm"
  pages=$(
    jq \
      --arg id "$pid" \
      --arg idx "$(idx_key "$i")" \
      --arg tmpl "$TEMPLATE" \
      --arg ts "$CREATED_TIME_MS" \
      '. += [{
         id: $id,
         idx: { timestamp: "1:2", value: $idx },
         modifed: $ts,
         template: { timestamp: "1:1", value: $tmpl }
       }]' <<<"$pages"
  )
  i=$((i + 1))
done

jq --argjson pages "$pages" --argjson n "$PAGES" --arg uuid "$AUTHOR_UUID" \
  '.cPages.pages = $pages
   | .cPages.lastOpened = { timestamp: "1:1", value: $pages[0].id }
   | .cPages.uuids = [ { first: $uuid, second: 1 } ]
   | .pageCount = $n' \
  "$BASE_CONTENT" >"$WORK/$DOCID.content"

jq -n --arg name "$NAME" --arg ts "$CREATED_TIME_MS" \
  '{
     createdTime: $ts,
     lastModified: $ts,
     lastOpened: "0",
     lastOpenedPage: -1,
     new: true,
     parent: "",
     pinned: false,
     source: "",
     type: "DocumentType",
     visibleName: $name
   }' >"$WORK/$DOCID.metadata"

OUT_ABS=$(CDPATH= cd -- "$(dirname -- "$OUTPUT")" && pwd)/$(basename -- "$OUTPUT")
rm -f "$OUT_ABS"
(cd "$WORK" && zip -r -X -q "$OUT_ABS" "$DOCID.content" "$DOCID.metadata" "$DOCID")

echo "Generated: $OUT_ABS"
echo "  name=$NAME  template=$TEMPLATE  pages=$PAGES  doc=$DOCID"
