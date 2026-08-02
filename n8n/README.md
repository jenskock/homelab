# n8n

Self-hosted n8n behind Traefik at `n8n.jenskock.de`.

## Services

| Service | Image / build | Role |
| --- | --- | --- |
| `n8n` | `docker.n8n.io/n8nio/n8n:latest` | Workflows |
| `gotenberg` | `gotenberg/gotenberg:8` | HTML → PDF |
| `article-extractor` | [`./article-extractor`](article-extractor/) | RSS + consent + article extract → PDF |
| `rmapi` | [`./rmapi`](rmapi/) | reMarkable Cloud uploads |

## Host paths

| Host | Container | Purpose |
| --- | --- | --- |
| `/opt/n8n/.env` | (env_file) | Secrets / config |
| `/opt/n8n/data` | `/home/node/.n8n` | n8n data |
| `/opt/n8n/rmapi-staging` | see [rmapi/README](rmapi/README.md) | Upload staging |
| `/opt/n8n/rmapi` | see [rmapi/README](rmapi/README.md) | rmapi auth |

## Setup

```bash
# Copy env.example → /opt/n8n/.env and set N8N_ENCRYPTION_KEY
cd /path/to/homelab/n8n
docker compose up -d --build
```

Workflow JSON lives in [`workflows/`](workflows/).
reMarkable pairing and the upload workflow:
[rmapi/README.md](rmapi/README.md).

## Workflows

| Workflow | Schedule | Output |
| --- | --- | --- |
| `nzz-mail-remarkable` | IMAP (IDLE + reconnect 15m) | `/News/YYYY-MM-DD/<subject>.pdf` |
| `rss-to-remarkable` | 07:00 daily | `/News/YYYY-MM-DD/<Publisher>-<Topic>.pdf` |
| `meeting-to-remarkable` | Webhook `POST /webhook/meeting-to-remarkable` | `/Work/Meetings/<title>.rmdoc` |
| `remarkable-upload` | (sub-workflow) | uploads PDF / `.rmdoc` via rmapi |

### `meeting-to-remarkable`

Lined `.rmdoc` notebook (5 pages, `P Lines medium`). Webhook uses n8n
**Header Auth** credential `Meeting Webhook` (create on import; not in
`.env`). Optional `folder` (default `/Work/Meetings`).

```bash
curl -sS -X POST "https://n8n.jenskock.de/webhook/meeting-to-remarkable" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: <value from Header Auth credential>" \
  -d '{
    "title": "Q3 Planning",
    "start": "2026-08-03T10:00:00+02:00",
    "end": "2026-08-03T11:00:00+02:00",
    "attendees": ["Alice", "Bob"],
    "location": "Zoom",
    "agenda": "1. Goals\n2. Risks",
    "notes": "Optional freeform notes"
  }'
```
