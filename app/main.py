from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .data import scan_projects_dir, build_projects

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    sessions = scan_projects_dir()
    projects = build_projects(sessions)

    items = ""
    for p in projects:
        items += f"<li>{p.display_name} ({p.session_count} sessions, {p.total_user_messages} prompts)</li>\n"

    return f"""
    <h1>Claude Code Viewer</h1>
    <p>{len(projects)} projects</p>
    <ul>
    {items}
    </ul>
    """
