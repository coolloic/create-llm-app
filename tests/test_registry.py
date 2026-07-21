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
