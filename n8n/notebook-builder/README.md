# notebook-builder

Builds native reMarkable `.rmdoc` notebooks with typed text (via
[rmscene](https://github.com/ricklupton/rmscene)).

## API

`POST /v1/meeting-rmdoc` — JSON body → `.rmdoc` bytes.

```bash
curl -sS -X POST http://127.0.0.1:8081/v1/meeting-rmdoc \
  -H 'content-type: application/json' \
  -d '{"title":"Q3 Planning","agenda":"1. Goals","attendees":["Alice"]}' \
  -o /tmp/meeting.rmdoc
```

## Local

```bash
cd n8n/notebook-builder
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8081
```
