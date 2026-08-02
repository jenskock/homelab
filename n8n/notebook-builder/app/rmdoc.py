from __future__ import annotations

import io
import json
import time
import zipfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from rmscene import simple_text_document, write_blocks

BASE_CONTENT_PATH = Path(__file__).resolve().parent.parent / "assets" / "base.content.json"
ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BERLIN = ZoneInfo("Europe/Berlin")


def idx_key(i: int) -> str:
    num = 2330 + i - 1
    return f"{ALPHA[num // 62]}{ALPHA[num % 62]}"


def sanitize_filename(name: str) -> str:
    ascii_name = (
        name.replace("ß", "ss")
        .replace("ẞ", "SS")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    base = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in ascii_name)
    while "--" in base:
        base = base.replace("--", "-")
    base = base.strip(".-") or "Meeting"
    return base if base.endswith(".rmdoc") else f"{base}.rmdoc"


def parse_datetime(value: str) -> datetime | None:
    raw = value.strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BERLIN)
    return dt.astimezone(BERLIN)


def format_when(value: str) -> str:
    dt = parse_datetime(value)
    if dt is None:
        return value.strip()
    return dt.strftime("%d.%m.%Y %H:%M")


def meeting_display_name(title: str, start: str = "") -> str:
    dt = parse_datetime(start) or datetime.now(tz=BERLIN)
    stamp = dt.strftime("%y-%m-%d")
    name = title.strip() or "Meeting"
    return f"{stamp} {name}"


def format_meeting_text(
    *,
    title: str,
    start: str = "",
    end: str = "",
    location: str = "",
    attendees: list[str] | None = None,
    agenda: str = "",
    notes: str = "",
) -> str:
    lines = [title.strip() or "Meeting", ""]

    start_fmt = format_when(start)
    end_fmt = format_when(end)
    if start_fmt and end_fmt:
        lines.append(f"When: {start_fmt} – {end_fmt}")
    elif start_fmt or end_fmt:
        lines.append(f"When: {start_fmt or end_fmt}")
    if location:
        lines.append(f"Location: {location}")
    if attendees:
        lines.append(f"Attendees: {', '.join(attendees)}")
    if agenda.strip():
        lines.extend(["", "Agenda", agenda.strip()])
    if notes.strip():
        lines.extend(["", "Notes", notes.strip()])

    return "\n".join(lines).rstrip() + "\n"


def build_rmdoc(
    *,
    title: str,
    text: str,
    start: str = "",
    template: str = "Blank",
    tags: list[str] | None = None,
) -> tuple[bytes, str]:
    author = uuid4()
    doc_id = str(uuid4())
    page_id = str(uuid4())
    created_ms = str(int(time.time() * 1000))
    display_name = meeting_display_name(title, start)
    filename = sanitize_filename(display_name)

    rm_buf = io.BytesIO()
    write_blocks(rm_buf, simple_text_document(text, author_uuid=author))
    rm_bytes = rm_buf.getvalue()

    base = json.loads(BASE_CONTENT_PATH.read_text(encoding="utf-8"))
    pages = [
        {
            "id": page_id,
            "idx": {"timestamp": "1:2", "value": idx_key(1)},
            "modifed": created_ms,
            "template": {"timestamp": "1:1", "value": template},
        }
    ]
    content = {
        **base,
        "cPages": {
            **base["cPages"],
            "pages": pages,
            "lastOpened": {"timestamp": "1:1", "value": page_id},
            "uuids": [{"first": str(author), "second": 1}],
        },
        "pageCount": 1,
        "tags": [{"name": t} for t in (tags or []) if t],
    }
    metadata = {
        "createdTime": created_ms,
        "lastModified": created_ms,
        "lastOpened": "0",
        "lastOpenedPage": -1,
        "new": True,
        "parent": "",
        "pinned": False,
        "source": "",
        "type": "DocumentType",
        "visibleName": display_name,
    }

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr(f"{doc_id}.content", json.dumps(content, separators=(",", ":")))
        zf.writestr(f"{doc_id}.metadata", json.dumps(metadata, separators=(",", ":")))
        zf.writestr(f"{doc_id}/{page_id}.rm", rm_bytes)
    return out.getvalue(), filename
