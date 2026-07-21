import py_compile

import pytest

from create_llm_app.config import ProjectConfig
from create_llm_app.generator import generate_project


def test_generate_chat_project(tmp_path):
    cfg = ProjectConfig(name="chatapp", provider="anthropic", app_type="chat")
    written = generate_project(cfg, tmp_path)

    proj = tmp_path / "chatapp"
    names = {p.name for p in written}
    assert names == {".env.example", ".gitignore", "requirements.txt", "README.md", "main.py"}
    assert (proj / "main.py").exists()

    main = (proj / "main.py").read_text()
    assert "load_dotenv()" in main
    assert "from langchain_anthropic import ChatAnthropic" in main
    assert "claude-opus-4-8" in main

    env = (proj / ".env.example").read_text()
    assert "ANTHROPIC_API_KEY=" in env

    reqs = (proj / "requirements.txt").read_text()
    assert "python-dotenv" in reqs
    assert "langchain-anthropic" in reqs

    # Generated main.py must be syntactically valid Python
    py_compile.compile(str(proj / "main.py"), doraise=True)


def test_generate_refuses_existing_dir(tmp_path):
    (tmp_path / "dupe").mkdir()
    with pytest.raises(FileExistsError):
        generate_project(ProjectConfig(name="dupe"), tmp_path)
