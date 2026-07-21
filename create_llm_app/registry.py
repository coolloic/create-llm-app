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
