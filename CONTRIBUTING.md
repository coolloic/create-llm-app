# Contributing to create-llm-app

Thanks for your interest in improving `create-llm-app`! This guide covers how to
set up the project, run the tests, and add the two most common extensions: a new
**provider** or a new **app type**.

## Development setup

Requires **Python ≥ 3.10**.

```bash
git clone https://github.com/coolloic/create-llm-app.git
cd create-llm-app

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[dev]"            # editable install + pytest
```

The editable install puts the `create-llm-app` command on your PATH and picks up
code changes without reinstalling. **Exception:** if you add or rename files under
`create_llm_app/templates/`, re-run `pip install -e ".[dev]"` so the packaged
templates are refreshed (they load via `jinja2.PackageLoader`).

## Running the tests

```bash
pytest -v                          # full suite
pytest tests/test_generator_rag.py -v   # a single file
```

All tests must pass before a change is merged. CI runs the same suite on Python
3.10–3.13 for every pull request.

The generator tests verify that the code they emit is **valid Python** by calling
`py_compile` on the rendered `main.py` — they do **not** run any LLM or hit the
network, so the suite is fully offline and fast.

## Project layout

```
create_llm_app/
├── config.py       # ProjectConfig dataclass + validation, VALID_* constants
├── registry.py     # ProviderSpec, PROVIDERS dict, build_context()
├── prompts.py      # collect_config() — interactive/flag config collection
├── generator.py    # generate_project() — renders templates to a project dir
├── cli.py          # Typer `new` command wiring
└── templates/      # Jinja2 templates (*.j2) + static sample data
tests/              # one test file per module / app type
```

Each module has one responsibility. Keep files focused; prefer adding a small,
well-named unit over growing an existing file.

## How to add a new provider

Example: adding **Google Gemini**.

1. **`config.py`** — add the key to `VALID_PROVIDERS`:
   ```python
   VALID_PROVIDERS = ("anthropic", "openai", "google")
   ```
2. **`registry.py`** — add a `ProviderSpec` entry to `PROVIDERS`:
   ```python
   "google": ProviderSpec(
       key="google",
       package="langchain-google-genai",
       import_path="langchain_google_genai",
       chat_class="ChatGoogleGenerativeAI",
       default_model="gemini-2.0-flash",
       env_var="GOOGLE_API_KEY",
   ),
   ```
3. **`tests/test_registry.py`** — add a test asserting each field of the new spec,
   and that `build_context` maps `default_model` to the `model` key.
4. Run `pytest -v`. The templates already consume `{{ import_path }}`,
   `{{ chat_class }}`, `{{ model }}`, and `{{ env_var }}`, so no template changes
   are needed for a standard chat-model provider.

## How to add a new app type

Example: adding a **summarizer** type.

1. **`config.py`** — add the key to `VALID_APP_TYPES`.
2. **`generator.py`** — add a `_MAIN_TEMPLATE` entry mapping the key to a template
   filename (e.g. `"summarizer": "main_summarizer.py.j2"`). Add any app-specific
   extra files the way the `rag` type writes `knowledge_base.txt`.
3. **`create_llm_app/templates/main_summarizer.py.j2`** — the generated `main.py`.
   Start it with `from dotenv import load_dotenv` and call `load_dotenv()` at the
   top (every generated app loads env via python-dotenv).
4. **`templates/requirements.txt.j2`** — add a `{% if app_type == 'summarizer' %}`
   block for any extra dependencies.
5. **`tests/test_generator_summarizer.py`** — assert the generated `main.py`
   contains the expected imports and `py_compile`s cleanly, and that
   `requirements.txt` includes the new dependencies.

## Coding conventions

- **TDD.** Write a failing test first, then the minimal code to pass it.
- **YAGNI / simplicity.** Add only what the change needs; no speculative options.
- Follow the existing style of the file you're editing. Type-annotate public
  function signatures (as `config.py`/`prompts.py` do).
- Every generated `main.py` must call `load_dotenv()` and be valid Python
  (covered by a `py_compile` assertion in its test).

## Commit & PR flow

- Use short, imperative commit subjects, ideally
  [Conventional Commits](https://www.conventionalcommits.org/) style:
  `feat:`, `fix:`, `test:`, `docs:`, `ci:`, `style:`.
- Open a pull request against `main`. CI (pytest on Python 3.10–3.13) must pass
  before merge; keep your branch up to date with `main`.
- Keep PRs focused — one logical change per PR, with tests included.

## License

By contributing, you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
