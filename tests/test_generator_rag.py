import py_compile

from create_llm_app.config import ProjectConfig
from create_llm_app.generator import generate_project


def test_generate_rag_project(tmp_path):
    cfg = ProjectConfig(name="ragapp", provider="anthropic", app_type="rag")
    written = generate_project(cfg, tmp_path)
    proj = tmp_path / "ragapp"

    names = {p.name for p in written}
    assert "knowledge_base.txt" in names
    assert (proj / "knowledge_base.txt").exists()

    main = (proj / "main.py").read_text()
    assert "load_dotenv()" in main
    assert "FAISS" in main
    assert "RecursiveCharacterTextSplitter" in main

    reqs = (proj / "requirements.txt").read_text()
    assert "faiss-cpu" in reqs

    py_compile.compile(str(proj / "main.py"), doraise=True)
