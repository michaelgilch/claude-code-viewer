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


@app.get("/project/{slug}", response_class=HTMLResponse)
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

    slug = _path_to_slug(project.original_path)
    items = ""
    for s in project.sessions:
        prompt = (s.first_prompt or "(no prompt)")[:80]
        items += f'<li><a href="/project/{slug}/session/{s.session_id}">{s.session_id[:8]}</a> - {prompt} ({s.user_message_count} prompts, {s.tool_call_count} tools)</li>\n'

    return f"""
    <h1>{project.display_name}</h1>
    <p>{project.original_path}</p>
    <p>{project.session_count} sessions</p>
    <ul>
    {items}
    </ul>
    <p><a href="/">Back</a></p>
    """


@app.get("/project/{slug}/session/{session_id}", response_class=HTMLResponse)
def session_detail(slug: str, session_id: str):
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

    session = None
    for s in project.sessions:
        if s.session_id == session_id:
            session = s
            break

    if not session:
        return "<h1>Session not found</h1>"

    messages_html = ""
    for m in session.messages:
        if m.role == "user" and m.text and not m.has_tool_result:
            messages_html += f'<div style="margin:1em 0;padding:0.5em;background:#eeeeff;border-left:3px solid #4a9eff"><b>User:</b><br>{m.text}</div>\n'
        elif m.role == "assistant" and m.text:
            messages_html += f'<div style="margin:1em 0;padding:0.5em;background:#ccddcc;border-left:3px solid #4aff9e"><b>Assistant:</b><br>{m.text[:500]}</div>\n'
        elif m.role == "assistant" and m.tool_name:
            messages_html += f'<div style="margin:1em 0;padding:0.5em;background:#eedddd;border-left:3px solid #ffcc4a"><b>Tool:</b> {m.tool_name}</div>\n'

    slug = _path_to_slug(project.original_path)
    return f"""
    <h1>Session {session.session_id[:8]}</h1>
    <p>{session.first_timestamp} - {session.last_timestamp}</p>
    <p>{session.user_message_count} prompts, {session.tool_call_count} tool calls</p>
    {messages_html}
    <p><a href="/project/{slug}">Back to {project.display_name}</a></p>
    """
