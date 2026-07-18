# Paperless-AI setup hint

In the Paperless-AI setup UI, set the Paperless URL to:

```text
http://paperless:8000
```

**Do not** add `/api` — the wizard appends it. Entering `…/api` becomes `…/api/api` and breaks scanning (`Failed to get own user ID`).

Fix if already wrong:

```bash
docker exec -u 0 paperless-ai sed -i \
  's|PAPERLESS_API_URL=.*|PAPERLESS_API_URL=http://paperless:8000/api|' \
  /app/data/.env
docker restart paperless-ai
```
