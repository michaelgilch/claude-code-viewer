"""
FastAPI web application for browsing Claude Code conversation history.

Routes:
    /                                   - List all projects
    /project/{slug}                     - List sessions for a project
    /project/{slug}/session/{session_id} - View a conversation

Each route loads data from ~/.claude/projects/ via scan_projects_dir() and
build_projects(), then passes the results to a Jinja2 template for rendering.

The `request` parameter on every route is required by Jinja2Templates -- it
uses the request to build URLs and set response headers.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .data import scan_projects_dir, build_projects

app = FastAPI()

# Point Jinja2 at app/templates/. Path(__file__).parent resolves to the app/
# directory regardless of where the server is started from.
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _find_project(projects, slug):
    """Find a project by its slug (the Claude Code directory name)."""
    for p in projects:
        if p.slug == slug:
            return p
    return None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """List all projects with session and prompt counts."""
    sessions = scan_projects_dir()
    projects = build_projects(sessions)
    return templates.TemplateResponse(request, "home.html", {"projects": projects})


@app.get("/project/{slug}", response_class=HTMLResponse)
def project_detail(request: Request, slug: str):
    """List all sessions for a single project."""
    sessions = scan_projects_dir()
    projects = build_projects(sessions)

    project = _find_project(projects, slug)
    if not project:
        return HTMLResponse("<h1>Project not found</h1>", status_code=404)

    return templates.TemplateResponse(request, "project.html", {"project": project})


@app.get("/project/{slug}/session/{session_id}", response_class=HTMLResponse)
def session_detail(request: Request, slug: str, session_id: str):
    """Display the conversation messages for a single session."""
    sessions = scan_projects_dir()
    projects = build_projects(sessions)

    project = _find_project(projects, slug)
    if not project:
        return HTMLResponse("<h1>Project not found</h1>", status_code=404)

    session = None
    for s in project.sessions:
        if s.session_id == session_id:
            session = s
            break

    if not session:
        return HTMLResponse("<h1>Session not found</h1>", status_code=404)

    # Both project and session are passed so the template can build
    # the "Back to <project>" link.
    return templates.TemplateResponse(request, "session.html", {
        "project": project,
        "session": session,
    })
