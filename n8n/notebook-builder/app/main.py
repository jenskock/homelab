from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.rmdoc import build_rmdoc, format_meeting_text

app = FastAPI(title="notebook-builder", version="1.0.0")


class MeetingNotebookRequest(BaseModel):
    title: str = Field(min_length=1)
    start: str = ""
    end: str = ""
    location: str = ""
    attendees: list[str] = Field(default_factory=list)
    agenda: str = ""
    notes: str = ""
    template: str = "Blank"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/meeting-rmdoc")
def meeting_rmdoc(req: MeetingNotebookRequest) -> Response:
    title = req.title.strip()
    attendees = [a.strip() for a in req.attendees if str(a).strip()]
    text = format_meeting_text(
        title=title,
        start=req.start.strip(),
        end=req.end.strip(),
        location=req.location.strip(),
        attendees=attendees,
        agenda=req.agenda,
        notes=req.notes,
    )

    tags = ["meeting"]
    if req.location.strip():
        tags.append(req.location.strip())
    if attendees:
        tags.append(", ".join(attendees))

    rmdoc, filename = build_rmdoc(
        title=title,
        text=text,
        start=req.start.strip(),
        template=req.template.strip() or "Blank",
        tags=tags,
    )

    return Response(
        content=rmdoc,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Filename": filename,
        },
    )
