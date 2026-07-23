from pathlib import Path

from jinja2 import Environment, PackageLoader

from .config import ProjectConfig
from .registry import build_context

_MAIN_TEMPLATE = {
    "chat": "main_chat.py.j2",
    "rag": "main_rag.py.j2",
    "agent": "main_agent.py.j2",
}

_COMMON_FILES = {
    ".env.example": "env.example.j2",
    ".gitignore": "gitignore.j2",
    "requirements.txt": "requirements.txt.j2",
    "README.md": "project_readme.md.j2",
}


def _env() -> Environment:
    return Environment(
        loader=PackageLoader("create_llm_app", "templates"),
        keep_trailing_newline=True,
    )


def generate_project(config: ProjectConfig, target_dir) -> list[Path]:
    project_dir = Path(target_dir) / config.name
    project_dir.mkdir(parents=True, exist_ok=False)  # raises FileExistsError if present

    ctx = build_context(config)
    env = _env()
    written: list[Path] = []

    files = dict(_COMMON_FILES)
    files["main.py"] = _MAIN_TEMPLATE[config.app_type]

    for out_name, template_name in files.items():
        content = env.get_template(template_name).render(**ctx)
        path = project_dir / out_name
        path.write_text(content)
        written.append(path)

    if config.app_type == "rag":
        content = env.get_template("knowledge_base.txt").render(**ctx)
        path = project_dir / "knowledge_base.txt"
        path.write_text(content)
        written.append(path)

    return written
