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

## Learn more

The generated **`rag`** app stores document chunks in an in-memory FAISS index.
To understand that storage layer — how vector databases work and how to swap
FAISS for Chroma, Qdrant, Pinecone, or pgvector (with full store-chunk
examples) — see the companion guide:
[**Vector Databases**](https://github.com/coolloic/Notebook/blob/main/vector-databases.md).
For the broader LangChain / LangGraph / LangSmith picture, see
[this guide](https://github.com/coolloic/Notebook/blob/main/README.md).
