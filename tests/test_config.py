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
