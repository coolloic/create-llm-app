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
