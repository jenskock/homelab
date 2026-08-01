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
| `nzz-briefing-remarkable` | 08:00 Mon–Sat | `/News/YYYY-MM-DD/NZZ-Briefing.pdf` |
| `rss-to-remarkable` | 07:00 daily | `/News/YYYY-MM-DD/<Publisher>-<Topic>.pdf` |
| `remarkable-upload` | (sub-workflow) | uploads PDF via rmapi |

### RSS → reMarkable

1. `docker compose up -d --build article-extractor gotenberg`
2. Import `workflows/rss-to-remarkable.json` (and `remarkable-upload` if needed)
3. Edit **Config Feeds** to add/remove feeds
4. Each morning: previous Berlin day → `/News/<day>/<Publisher>-<Topic>.pdf`

See [article-extractor/README.md](article-extractor/README.md) for local tests.
