# rmapi (reMarkable upload worker)

Drop-folder worker used by n8n to upload files to reMarkable Cloud
via [ddvk/rmapi](https://github.com/ddvk/rmapi).

n8n writes a document + `.meta.json` into a shared staging volume; this
container watches the outbox and runs `rmapi put --force`.

Supported outbox extensions: `.pdf`, `.rmdoc`, `.rmn`, `.zip`.

## Layout

| Host | n8n | rmapi | Purpose |
| --- | --- | --- | --- |
| `/opt/n8n/rmapi-staging` | `/home/node/.n8n-files` | `/data` | staging dirs |
| `/opt/n8n/rmapi` | — | `~/.config/rmapi` | auth (`rmapi.conf`) |

n8n path: `/home/node/.n8n-files`
(`outbox/` / `done/` / `failed/`).

## Build & start

From the parent `n8n/` compose directory:

```bash
sudo mkdir -p /opt/n8n/rmapi \
  /opt/n8n/rmapi-staging/{outbox,done,failed}
sudo chown -R 1000:1000 /opt/n8n/rmapi /opt/n8n/rmapi-staging

# Add NODE_FUNCTION_ALLOW_BUILTIN=fs from ../env.example to /opt/n8n/.env
docker compose build rmapi
docker compose up -d
```

## Pairing

1. Get an 8-character code at
   [my.remarkable.com device connect](https://my.remarkable.com/device/browser/connect)
   (~5 min validity).
2. Override the watch entrypoint and log in:

   ```bash
   docker exec -it -u 1000 \
     -e RMAPI_CONFIG=/home/node/.config/rmapi/rmapi.conf \
     n8n-rmapi rmapi
   ```

3. Token lands in `/opt/n8n/rmapi/rmapi.conf` (uid 1000).
   Verify with `rmapi ls`.
4. Re-pair: delete that file and repeat.
   Device-token TTL is undocumented by rmapi.

## Test

Import
[`../workflows/remarkable-upload.json`](../workflows/remarkable-upload.json),
run **Manual Trigger**, confirm the smoke PDF in `/Inbox`.

## Caller contract

Execute Workflow → `remarkable-upload` with:

| Field | Required | Example |
| --- | --- | --- |
| `binary.data` | yes | PDF or `.rmdoc` bytes |
| `json.filename` | yes | `NZZ-Briefing.pdf` or `Q3-Planning.rmdoc` |
| `json.folder` | no | `/News/2026-07-30` (default `/Inbox`) |

`folder` is any absolute cloud path (e.g. `/Work/Meetings` or
`/Work/My Projects`); nested folders are created as needed.

Sidecar: `outbox/<base>.<ext>` +
`outbox/<base>.<ext>.meta.json` → `{ "folder", "name" }`.

## Native notebooks

[`notebook/`](notebook/) — blank-page stencil + `build-rmdoc` (in image):

```bash
build-rmdoc "Meeting Title" /tmp/meeting.rmdoc 5 "P Lines medium"
rmapi put --force -- /tmp/meeting.rmdoc /Work/Meetings
```

## Troubleshoot

| Symptom | Check |
| --- | --- |
| Bad token | Delete `rmapi.conf`, re-pair; check logs |
| Stuck in outbox | Worker running? Meta present? |
| Permission errors | `chown -R 1000:1000` on rmapi dirs |
| Arch / missing binary | `docker compose build --no-cache rmapi` |
| Workflow timeout | `failed/*.err`, pairing, network |
| `Cannot find module 'fs'` | Set `NODE_FUNCTION_ALLOW_BUILTIN=fs` |

**User token HTTP 400 after pairing:** reMarkable requires a physical
tablet already connected to the same cloud account. With
`RMAPI_TRACE=1`, the body is: *You must connect a rM device in the
webapp before you can use this service.* Connect the tablet first,
then re-run rmapi login.

**`compose … not found`:** run compose from the repo `n8n/` directory
(where `docker-compose.yml` lives), or use `docker exec` as above.

## Verified vs best-effort

Verified: fork `ddvk/rmapi` v0.0.34 asset names, pairing URL,
`RMAPI_CONFIG`, `put --force` overwrite.

Best-effort: one-time code TTL (~5 min), device-token lifetime,
`.rmdoc` / `.rmn` upload via the same `put` path as PDF.
amd64 release binary is glibc-linked; image installs `libc6-compat`.
