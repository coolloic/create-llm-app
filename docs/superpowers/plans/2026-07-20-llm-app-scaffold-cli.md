# LLM App Scaffold CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `create-llm-app` CLI that scaffolds a runnable LLM application, letting the user choose the provider, app type, and observability, with environment loaded via python-dotenv.

**Architecture:** A Typer CLI collects a `ProjectConfig` (via flags or interactive `questionary` prompts), a registry maps provider/app-type choices to concrete packages and code, and a Jinja2-based generator renders a self-contained project directory. Generation logic is a pure function (`generate_project`) so it is fully unit-testable without running any LLM.

**Tech Stack:** Python 3.10+, Typer (CLI), questionary (interactive prompts), Jinja2 (templating), pytest (tests), hatchling (build). Generated projects use LangChain / LangGraph / LangSmith + python-dotenv.

## Global Constraints

- **Python version floor:** `requires-python = ">=3.10"` (uses `X | None` unions and modern typing) — copy verbatim into `pyproject.toml`.
- **CLI package name:** `create-llm-app`; **import package:** `create_llm_app`; **console entry point:** `create-llm-app = "create_llm_app.cli:app"`.
- **Providers supported (MVP):** `anthropic`, `openai` only.
- **App types supported (MVP):** `chat`, `rag`, `agent` only.
- **Generated projects MUST load env via python-dotenv** (`load_dotenv()` at top of every `main.py`).
- **Anthropic default model string:** `claude-opus-4-8`. **OpenAI default model string:** `gpt-4o`.
- **No network / no real LLM calls in tests.** Generated code is verified by byte-compilation (`py_compile`), never by execution.
- **TDD:** every task writes a failing test first. Commit after each task.

---

## File Structure

```
create-llm-app/
├── pyproject.toml                 # package metadata, deps, entry point
├── README.md                      # CLI usage docs
├── create_llm_app/
│   ├── __init__.py
│   ├── cli.py                     # Typer app + `new` command (wiring only)
│   ├── config.py                  # ProjectConfig dataclass + validation + constants
│   ├── registry.py                # ProviderSpec, PROVIDERS, get_provider, build_context
│   ├── prompts.py                 # collect_config (fills missing fields interactively)
│   ├── generator.py               # generate_project (pure file-writing function)
│   └── templates/
│       ├── env.example.j2
│       ├── gitignore.j2
│       ├── requirements.txt.j2
│       ├── project_readme.md.j2
│       ├── main_chat.py.j2
│       ├── main_rag.py.j2
│       ├── main_agent.py.j2
│       └── knowledge_base.txt     # sample RAG data (rendered as a template, no vars)
└── tests/
    ├── test_cli.py
    ├── test_config.py
    ├── test_registry.py
    ├── test_generator_chat.py
    ├── test_generator_rag.py
    ├── test_generator_agent.py
    └── test_prompts.py
```

All commands below are run from the repository root (`create-llm-app/`).

---

## Task 1: Project bootstrap & CLI skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `create_llm_app/__init__.py`
- Create: `create_llm_app/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: a Typer `app` object in `create_llm_app.cli` with a `new` command taking `name: str` and printing a placeholder. Console script `create-llm-app`.

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:
```python
from typer.testing import CliRunner
from create_llm_app.cli import app

runner = CliRunner()

def test_new_command_exists():
    result = runner.invoke(app, ["new", "myapp"])
    assert result.exit_code == 0
    assert "myapp" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'create_llm_app'`.

- [ ] **Step 3: Create the package and pyproject**

`pyproject.toml`:
```toml
[project]
name = "create-llm-app"
version = "0.1.0"
description = "Scaffold runnable LLM applications (LangChain / LangGraph)."
requires-python = ">=3.10"
dependencies = ["typer>=0.12", "jinja2>=3.1", "questionary>=2.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
create-llm-app = "create_llm_app.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["create_llm_app"]

[tool.hatch.build.targets.wheel.force-include]
"create_llm_app/templates" = "create_llm_app/templates"
```

`create_llm_app/__init__.py`:
```python
__version__ = "0.1.0"
```

`create_llm_app/cli.py`:
```python
import typer

app = typer.Typer(help="Scaffold runnable LLM applications.")


@app.command()
def new(name: str = typer.Argument(..., help="Project directory name")):
    """Create a new LLM application in ./<name>."""
    typer.echo(f"(placeholder) would create project: {name}")


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Install the package editable and run the test**

Run: `python -m pip install -e ".[dev]" && python -m pytest tests/test_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml create_llm_app/__init__.py create_llm_app/cli.py tests/test_cli.py
git commit -m "feat: bootstrap create-llm-app CLI skeleton"
```

---

## Task 2: ProjectConfig model + validation

**Files:**
- Create: `create_llm_app/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - Constants `VALID_PROVIDERS = ("anthropic", "openai")`, `VALID_APP_TYPES = ("chat", "rag", "agent")`, `VALID_VECTOR_STORES = ("faiss", "chroma")`.
  - `@dataclass ProjectConfig(name: str, provider: str = "anthropic", app_type: str = "chat", tracing: bool = False, vector_store: str = "faiss")` that raises `ValueError` on invalid `name`, `provider`, `app_type`, or `vector_store`.

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
import pytest
from create_llm_app.config import ProjectConfig


def test_defaults():
    cfg = ProjectConfig(name="demo")
    assert cfg.provider == "anthropic"
    assert cfg.app_type == "chat"
    assert cfg.tracing is False
    assert cfg.vector_store == "faiss"


def test_invalid_name_rejected():
    with pytest.raises(ValueError):
        ProjectConfig(name="bad name!")


def test_invalid_provider_rejected():
    with pytest.raises(ValueError):
        ProjectConfig(name="demo", provider="cohere")


def test_invalid_app_type_rejected():
    with pytest.raises(ValueError):
        ProjectConfig(name="demo", app_type="wizard")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'create_llm_app.config'`.

- [ ] **Step 3: Write minimal implementation**

`create_llm_app/config.py`:
```python
import re
from dataclasses import dataclass

VALID_PROVIDERS = ("anthropic", "openai")
VALID_APP_TYPES = ("chat", "rag", "agent")
VALID_VECTOR_STORES = ("faiss", "chroma")

_NAME_RE = re.compile(r"[a-zA-Z0-9._-]+")


@dataclass
class ProjectConfig:
    name: str
    provider: str = "anthropic"
    app_type: str = "chat"
    tracing: bool = False
    vector_store: str = "faiss"

    def __post_init__(self):
        if not _NAME_RE.fullmatch(self.name):
            raise ValueError(f"Invalid project name: {self.name!r}")
        if self.provider not in VALID_PROVIDERS:
            raise ValueError(f"Unknown provider: {self.provider!r}")
        if self.app_type not in VALID_APP_TYPES:
            raise ValueError(f"Unknown app_type: {self.app_type!r}")
        if self.vector_store not in VALID_VECTOR_STORES:
            raise ValueError(f"Unknown vector_store: {self.vector_store!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add create_llm_app/config.py tests/test_config.py
git commit -m "feat: add ProjectConfig with validation"
```

---

## Task 3: Provider registry + template context

**Files:**
- Create: `create_llm_app/registry.py`
- Test: `tests/test_registry.py`

**Interfaces:**
- Consumes: `ProjectConfig` from `create_llm_app.config`.
- Produces:
  - `@dataclass(frozen=True) ProviderSpec(key, package, import_path, chat_class, default_model, env_var)` — all `str`.
  - `PROVIDERS: dict[str, ProviderSpec]` with `anthropic` and `openai` entries.
  - `get_provider(key: str) -> ProviderSpec` (raises `KeyError` on unknown).
  - `build_context(config: ProjectConfig) -> dict` returning keys: `name, provider, app_type, tracing, vector_store, package, import_path, chat_class, model, env_var`.

- [ ] **Step 1: Write the failing test**

`tests/test_registry.py`:
```python
import pytest
from create_llm_app.config import ProjectConfig
from create_llm_app.registry import get_provider, build_context


def test_get_provider_anthropic():
    spec = get_provider("anthropic")
    assert spec.package == "langchain-anthropic"
    assert spec.import_path == "langchain_anthropic"
    assert spec.chat_class == "ChatAnthropic"
    assert spec.default_model == "claude-opus-4-8"
    assert spec.env_var == "ANTHROPIC_API_KEY"


def test_get_provider_openai():
    spec = get_provider("openai")
    assert spec.chat_class == "ChatOpenAI"
    assert spec.env_var == "OPENAI_API_KEY"


def test_get_provider_unknown_raises():
    with pytest.raises(KeyError):
        get_provider("cohere")


def test_build_context_merges_provider_and_config():
    ctx = build_context(ProjectConfig(name="demo", provider="openai", app_type="rag", tracing=True))
    assert ctx["name"] == "demo"
    assert ctx["app_type"] == "rag"
    assert ctx["tracing"] is True
    assert ctx["chat_class"] == "ChatOpenAI"
    assert ctx["model"] == "gpt-4o"
    assert ctx["env_var"] == "OPENAI_API_KEY"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'create_llm_app.registry'`.

- [ ] **Step 3: Write minimal implementation**

`create_llm_app/registry.py`:
```python
from dataclasses import dataclass

from .config import ProjectConfig


@dataclass(frozen=True)
class ProviderSpec:
    key: str
    package: str
    import_path: str
    chat_class: str
    default_model: str
    env_var: str


PROVIDERS: dict[str, ProviderSpec] = {
    "anthropic": ProviderSpec(
        key="anthropic",
        package="langchain-anthropic",
        import_path="langchain_anthropic",
        chat_class="ChatAnthropic",
        default_model="claude-opus-4-8",
        env_var="ANTHROPIC_API_KEY",
    ),
    "openai": ProviderSpec(
        key="openai",
        package="langchain-openai",
        import_path="langchain_openai",
        chat_class="ChatOpenAI",
        default_model="gpt-4o",
        env_var="OPENAI_API_KEY",
    ),
}


def get_provider(key: str) -> ProviderSpec:
    return PROVIDERS[key]


def build_context(config: ProjectConfig) -> dict:
    spec = get_provider(config.provider)
    return {
        "name": config.name,
        "provider": config.provider,
        "app_type": config.app_type,
        "tracing": config.tracing,
        "vector_store": config.vector_store,
        "package": spec.package,
        "import_path": spec.import_path,
        "chat_class": spec.chat_class,
        "model": spec.default_model,
        "env_var": spec.env_var,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_registry.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add create_llm_app/registry.py tests/test_registry.py
git commit -m "feat: add provider registry and template context builder"
```

---

## Task 4: Generator core + chat template (runnable chat project)

**Files:**
- Create: `create_llm_app/generator.py`
- Create: `create_llm_app/templates/env.example.j2`
- Create: `create_llm_app/templates/gitignore.j2`
- Create: `create_llm_app/templates/requirements.txt.j2`
- Create: `create_llm_app/templates/project_readme.md.j2`
- Create: `create_llm_app/templates/main_chat.py.j2`
- Test: `tests/test_generator_chat.py`

**Interfaces:**
- Consumes: `ProjectConfig` (config.py), `build_context` (registry.py).
- Produces: `generate_project(config: ProjectConfig, target_dir) -> list[Path]` — creates `target_dir/<name>/`, renders the common files plus `main.py` for the app type, returns the list of written `Path`s. Raises `FileExistsError` if the target project dir already exists.

- [ ] **Step 1: Write the failing test**

`tests/test_generator_chat.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_generator_chat.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'create_llm_app.generator'`.

- [ ] **Step 3: Create the templates**

`create_llm_app/templates/env.example.j2`:
```
{{ env_var }}=your-key-here
{% if tracing -%}
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
{% endif -%}
```

`create_llm_app/templates/gitignore.j2`:
```
.env
__pycache__/
*.pyc
.venv/
```

`create_llm_app/templates/requirements.txt.j2`:
```
python-dotenv
langchain-core
{{ package }}
{% if app_type == 'rag' -%}
langchain-community
langchain-text-splitters
faiss-cpu
sentence-transformers
{% endif -%}
{% if app_type == 'agent' -%}
langgraph
{% endif -%}
{% if tracing -%}
langsmith
{% endif -%}
```

`create_llm_app/templates/project_readme.md.j2` (uses a `~~~` fenced block so the inner shell block doesn't clash):
~~~
# {{ name }}

A **{{ app_type }}** LLM application using `{{ chat_class }}` ({{ provider }}){% if tracing %}, with LangSmith tracing enabled{% endif %}.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in your API key(s)
python main.py
```

Environment variables are loaded automatically via **python-dotenv** (`load_dotenv()` in `main.py`).
~~~

`create_llm_app/templates/main_chat.py.j2`:
```
from dotenv import load_dotenv
from {{ import_path }} import {{ chat_class }}
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

model = {{ chat_class }}(model="{{ model }}", temperature=0)
prompt = ChatPromptTemplate.from_template("You are a helpful assistant. Answer: {question}")
chain = prompt | model | StrOutputParser()

if __name__ == "__main__":
    question = input("Ask something: ")
    print(chain.invoke({"question": question}))
```

- [ ] **Step 4: Write the generator**

`create_llm_app/generator.py`:
```python
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

    return written
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_generator_chat.py -v`
Expected: PASS (2 tests). If `PackageLoader` cannot find templates, re-run `python -m pip install -e ".[dev]"` so the editable install picks up the new `templates/` directory.

- [ ] **Step 6: Commit**

```bash
git add create_llm_app/generator.py create_llm_app/templates tests/test_generator_chat.py
git commit -m "feat: generate runnable chat project from templates"
```

---

## Task 5: RAG template

**Files:**
- Create: `create_llm_app/templates/main_rag.py.j2`
- Create: `create_llm_app/templates/knowledge_base.txt`
- Modify: `create_llm_app/generator.py` (add RAG-only extra file)
- Test: `tests/test_generator_rag.py`

**Interfaces:**
- Consumes: `generate_project` (task 4).
- Produces: when `app_type == "rag"`, the generated project additionally contains `knowledge_base.txt`; `main.py` is the RAG chain. `generate_project` return list includes the extra file.

- [ ] **Step 1: Write the failing test**

`tests/test_generator_rag.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_generator_rag.py -v`
Expected: FAIL — `jinja2.exceptions.TemplateNotFound: main_rag.py.j2`.

- [ ] **Step 3: Create the RAG templates**

`create_llm_app/templates/main_rag.py.j2`:
```
from dotenv import load_dotenv
from {{ import_path }} import {{ chat_class }}
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

docs = TextLoader("knowledge_base.txt").load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
retriever = FAISS.from_documents(chunks, embeddings).as_retriever(search_kwargs={"k": 4})

prompt = ChatPromptTemplate.from_template(
    "Answer using ONLY this context:\n{context}\n\nQuestion: {question}"
)
model = {{ chat_class }}(model="{{ model }}", temperature=0)


def format_docs(documents):
    return "\n\n".join(d.page_content for d in documents)


chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

if __name__ == "__main__":
    question = input("Ask about the knowledge base: ")
    print(chain.invoke(question))
```

`create_llm_app/templates/knowledge_base.txt`:
```
Our refund policy allows returns within 30 days of purchase.
Shipping fees are non-refundable.
The customer pays for return shipping.
```

- [ ] **Step 4: Add the RAG-only extra file to the generator**

In `create_llm_app/generator.py`, add — immediately before `return written` inside `generate_project`:
```python
    if config.app_type == "rag":
        content = env.get_template("knowledge_base.txt").render(**ctx)
        path = project_dir / "knowledge_base.txt"
        path.write_text(content)
        written.append(path)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_generator_rag.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add create_llm_app/templates/main_rag.py.j2 create_llm_app/templates/knowledge_base.txt create_llm_app/generator.py tests/test_generator_rag.py
git commit -m "feat: add RAG app template with sample knowledge base"
```

---

## Task 6: Agent template

**Files:**
- Create: `create_llm_app/templates/main_agent.py.j2`
- Test: `tests/test_generator_agent.py`

**Interfaces:**
- Consumes: `generate_project` (task 4) — the `_MAIN_TEMPLATE["agent"]` entry already points at `main_agent.py.j2`.
- Produces: when `app_type == "agent"`, `main.py` is a LangGraph tool-using agent; `requirements.txt` includes `langgraph`.

- [ ] **Step 1: Write the failing test**

`tests/test_generator_agent.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_generator_agent.py -v`
Expected: FAIL — `jinja2.exceptions.TemplateNotFound: main_agent.py.j2`.

- [ ] **Step 3: Create the agent template**

`create_llm_app/templates/main_agent.py.j2`:
```
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from {{ import_path }} import {{ chat_class }}
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression, e.g. '3 * (4 + 2)'."""
    return str(eval(expression, {"__builtins__": {}}))


tools = [calculator]
model = {{ chat_class }}(model="{{ model }}", temperature=0).bind_tools(tools)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def call_model(state: State):
    return {"messages": [model.invoke(state["messages"])]}


builder = StateGraph(State)
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
graph = builder.compile(checkpointer=MemorySaver())

if __name__ == "__main__":
    question = input("Ask the agent: ")
    result = graph.invoke(
        {"messages": [HumanMessage(question)]},
        {"configurable": {"thread_id": "cli"}},
    )
    print(result["messages"][-1].content)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_generator_agent.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add create_llm_app/templates/main_agent.py.j2 tests/test_generator_agent.py
git commit -m "feat: add LangGraph agent app template"
```

---

## Task 7: Interactive prompts

**Files:**
- Create: `create_llm_app/prompts.py`
- Test: `tests/test_prompts.py`

**Interfaces:**
- Consumes: `ProjectConfig`, `VALID_PROVIDERS`, `VALID_APP_TYPES` (config.py).
- Produces: `collect_config(name: str, provider: str | None, app_type: str | None, tracing: bool | None) -> ProjectConfig`. Any argument that is `None` is filled by asking the user via `questionary`; any argument provided is used as-is (no prompt). When all of `provider`, `app_type`, `tracing` are non-`None`, `questionary` is never called.

- [ ] **Step 1: Write the failing test**

`tests/test_prompts.py`:
```python
import create_llm_app.prompts as prompts_mod
from create_llm_app.prompts import collect_config


def test_all_flags_provided_skips_questionary(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("questionary should not be called when all flags are provided")

    monkeypatch.setattr(prompts_mod, "questionary", type("Q", (), {"select": boom, "confirm": boom}))

    cfg = collect_config("demo", provider="openai", app_type="agent", tracing=False)
    assert cfg.provider == "openai"
    assert cfg.app_type == "agent"
    assert cfg.tracing is False


def test_missing_fields_are_prompted(monkeypatch):
    class FakeAnswer:
        def __init__(self, value):
            self._value = value

        def ask(self):
            return self._value

    class FakeQuestionary:
        @staticmethod
        def select(message, choices):
            # return provider first call, app_type second call
            return FakeAnswer("anthropic" if "provider" in message.lower() else "rag")

        @staticmethod
        def confirm(message, default=False):
            return FakeAnswer(True)

    monkeypatch.setattr(prompts_mod, "questionary", FakeQuestionary)

    cfg = collect_config("demo", provider=None, app_type=None, tracing=None)
    assert cfg.provider == "anthropic"
    assert cfg.app_type == "rag"
    assert cfg.tracing is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prompts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'create_llm_app.prompts'`.

- [ ] **Step 3: Write minimal implementation**

`create_llm_app/prompts.py`:
```python
import questionary

from .config import ProjectConfig, VALID_APP_TYPES, VALID_PROVIDERS


def collect_config(name, provider, app_type, tracing) -> ProjectConfig:
    if provider is None:
        provider = questionary.select("LLM provider?", choices=list(VALID_PROVIDERS)).ask()
    if app_type is None:
        app_type = questionary.select("App type?", choices=list(VALID_APP_TYPES)).ask()
    if tracing is None:
        tracing = questionary.confirm("Enable LangSmith tracing?", default=False).ask()
    return ProjectConfig(name=name, provider=provider, app_type=app_type, tracing=bool(tracing))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_prompts.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add create_llm_app/prompts.py tests/test_prompts.py
git commit -m "feat: add interactive config collection"
```

---

## Task 8: Wire the CLI end-to-end + project README

**Files:**
- Modify: `create_llm_app/cli.py`
- Create: `README.md` (CLI documentation)
- Test: `tests/test_cli.py` (replace the placeholder test)

**Interfaces:**
- Consumes: `collect_config` (prompts.py), `generate_project` (generator.py).
- Produces: the final `new` command:
  `create-llm-app new NAME [--provider/-p] [--type/-t] [--tracing/--no-tracing]` — builds a config (flags fill non-interactively; missing values would prompt) and writes the project into the current working directory, printing a success + next-steps message.

- [ ] **Step 1: Replace the CLI test with the end-to-end test**

`tests/test_cli.py` (full replacement):
```python
import py_compile
from pathlib import Path

from typer.testing import CliRunner

from create_llm_app.cli import app

runner = CliRunner()


def test_new_generates_project_with_flags(tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["new", "myapp", "--provider", "anthropic", "--type", "chat", "--no-tracing"],
        )
        assert result.exit_code == 0, result.output
        assert "myapp" in result.output

        proj = Path("myapp")
        assert (proj / "main.py").exists()
        assert (proj / "requirements.txt").exists()
        assert (proj / ".env.example").exists()

        # generated app is valid Python
        py_compile.compile(str(proj / "main.py"), doraise=True)


def test_new_rejects_invalid_provider(tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app,
            ["new", "myapp", "--provider", "cohere", "--type", "chat", "--no-tracing"],
        )
        assert result.exit_code != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL — the placeholder `new` command ignores flags and writes nothing (`main.py` does not exist).

- [ ] **Step 3: Implement the real `new` command**

`create_llm_app/cli.py` (full replacement):
```python
from pathlib import Path

import typer

from .generator import generate_project
from .prompts import collect_config

app = typer.Typer(help="Scaffold runnable LLM applications.")


@app.command()
def new(
    name: str = typer.Argument(..., help="Project directory name"),
    provider: str = typer.Option(None, "--provider", "-p", help="anthropic | openai"),
    app_type: str = typer.Option(None, "--type", "-t", help="chat | rag | agent"),
    tracing: bool = typer.Option(None, "--tracing/--no-tracing", help="Enable LangSmith tracing"),
):
    """Create a new runnable LLM application in ./<name>."""
    try:
        config = collect_config(name, provider, app_type, tracing)
        written = generate_project(config, Path.cwd())
    except (ValueError, FileExistsError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho(f"Created {config.name}/ with {len(written)} files.", fg=typer.colors.GREEN)
    typer.echo(f"Next steps:\n  cd {config.name}\n  pip install -r requirements.txt")
    typer.echo("  cp .env.example .env   # add your API key(s)\n  python main.py")


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Write the CLI README**

`README.md`:
~~~
# create-llm-app

Scaffold a **runnable** LLM application (LangChain / LangGraph) in seconds.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Fully interactive — prompts for provider, app type, and tracing
create-llm-app new my-assistant

# Or non-interactive with flags
create-llm-app new my-assistant --provider anthropic --type rag --no-tracing
```

### Options

| Flag | Values | Default |
|------|--------|---------|
| `--provider`, `-p` | `anthropic`, `openai` | prompted |
| `--type`, `-t` | `chat`, `rag`, `agent` | prompted |
| `--tracing / --no-tracing` | LangSmith on/off | prompted |

## What you get

A self-contained project with `main.py`, `requirements.txt`, `.env.example`,
`.gitignore`, and `README.md`. Environment variables load automatically via
**python-dotenv**.

```bash
cd my-assistant
pip install -r requirements.txt
cp .env.example .env    # add your API key(s)
python main.py
```
~~~

- [ ] **Step 6: Run the full test suite**

Run: `python -m pytest -v`
Expected: PASS (all tests across every file).

- [ ] **Step 7: Manual smoke test (optional but recommended)**

Run:
```bash
cd /tmp && rm -rf smoke && mkdir smoke && cd smoke
create-llm-app new demo --provider anthropic --type agent --no-tracing
python -m py_compile demo/main.py && echo "OK: generated agent compiles"
```
Expected: `OK: generated agent compiles`.

- [ ] **Step 8: Commit**

```bash
git add create_llm_app/cli.py tests/test_cli.py README.md
git commit -m "feat: wire create-llm-app new end-to-end + docs"
```

---

## Self-Review

**1. Spec coverage:**
- "CLI to create the scaffold" → Tasks 1, 8 (Typer `new` command).
- "choose what should be used" → Tasks 2, 3, 7 (config + registry + interactive/flag selection of provider, app type, tracing).
- "a runnable LLM application" → Tasks 4, 5, 6 (chat/rag/agent templates, each byte-compiled in tests) + Task 8 smoke test.
- "load env via dotenv" → every `main_*.py.j2` calls `load_dotenv()`; asserted in tasks 4/5/6 tests and the global constraints.

**2. Placeholder scan:** No `TBD`/`TODO`/"similar to Task N"/"add error handling" placeholders — every code and template block is complete.

**3. Type consistency:** `generate_project(config, target_dir) -> list[Path]`, `build_context(config) -> dict`, `get_provider(key) -> ProviderSpec`, and `collect_config(name, provider, app_type, tracing) -> ProjectConfig` are used with identical signatures in every consuming task and test. `_MAIN_TEMPLATE` keys (`chat`/`rag`/`agent`) match `VALID_APP_TYPES`. Provider fields (`import_path`, `chat_class`, `default_model`, `env_var`) match the template variables (`{{ import_path }}`, `{{ chat_class }}`, `{{ model }}`, `{{ env_var }}`) — note `default_model` is exposed to templates as `model` via `build_context`.