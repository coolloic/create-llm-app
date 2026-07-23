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
