import py_compile

from create_llm_app.config import ProjectConfig
from create_llm_app.generator import generate_project


def test_generate_agent_project(tmp_path):
    cfg = ProjectConfig(name="agentapp", provider="openai", app_type="agent", tracing=True)
    generate_project(cfg, tmp_path)
    proj = tmp_path / "agentapp"

    main = (proj / "main.py").read_text()
    assert "load_dotenv()" in main
    assert "from langgraph.graph import StateGraph" in main
    assert "from langchain_openai import ChatOpenAI" in main
    assert "gpt-4o" in main

    reqs = (proj / "requirements.txt").read_text()
    assert "langgraph" in reqs
    assert "langsmith" in reqs  # tracing=True

    env = (proj / ".env.example").read_text()
    assert "LANGSMITH_TRACING=true" in env

    py_compile.compile(str(proj / "main.py"), doraise=True)
