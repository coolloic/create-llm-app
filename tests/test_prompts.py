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
