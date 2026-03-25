from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .data import scan_projects_dir, build_projects

app = FastAPI()


def _path_to_slug(path: str) -> str:
    """Convert a path to a URL-safe slug, e.g. '/home/michael/git' -> '-home-michael-git'"""
    return path.replace("/", "-")


def _slug_to_path(slug: str) -> str:
    """Convert a slug back to a path, e.g. '-home-michael-git' -> '/home/michael/git'"""
    return slug.replace("-", "/")


@app.get("/", response_class=HTMLResponse)
def home():
    sessions = scan_projects_dir()
    projects = build_projects(sessions)

    items = ""
    for p in projects:
        slug = _path_to_slug(p.original_path)
        items += f'<li><a href="/project/{slug}">{p.display_name}</a> ({p.session_count} sessions, {p.total_user_messages} prompts)</li>\n'

    return f"""
    <h1>Claude Code Viewer</h1>
    <p>{len(projects)} projects</p>
    <ul>
    {items}
    </ul>
    """


@app.get("/project/{slug:path}", response_class=HTMLResponse)
def project_detail(slug: str):
    sessions = scan_projects_dir()
    projects = build_projects(sessions)

    original_path = _slug_to_path(slug)
    project = None
    for p in projects:
        if p.original_path == original_path:
            project = p
            break

    if not project:
        return "<h1>Project not found</h1>"

    items = ""
    for s in project.sessions:
        prompt = (s.first_prompt or "(no prompt)")[:80]
        items += f"<li>{s.session_id[:8]} - {prompt} ({s.user_message_count} prompts, {s.tool_call_count} tools)</li>\n"

    return f"""
    <h1>{project.display_name}</h1>
    <p>{project.original_path}</p>
    <p>{project.session_count} sessions</p>
    <ul>
    {items}
    </ul>
    <p><a href="/">Back</a></p>
    """
