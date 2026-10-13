"""Typed view of the ``[pr_parity]`` settings section.

Every knob the parity tool honours is read here and nowhere else, so a future dashboard
(or any other writer of ``.pr_agent.toml``) only has to know the flat key list in
``ParityConfig.FIELDS``. Keep the keys flat (no nested tables) and typed as str/bool/int/list
of str so they map 1:1 onto form fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pr_agent.config_loader import get_settings

SECTION = "pr_parity"

DEFAULT_LANGUAGES = ["typescript", "rust", "golang", "python"]
DEFAULT_SERVICE_DIR_PATTERNS = ["services/*", "apps/*", "cmd/*", "src/*/services/*", "src/*/apps/*"]
# Language -> file extensions used to work out which language a file under ``root`` belongs to when
# the directory name alone does not say (and to exclude non-code files from candidate ranking).
DEFAULT_LANGUAGE_EXTENSIONS: dict[str, list[str]] = {
    "typescript": [".ts", ".tsx", ".mts", ".cts"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "rust": [".rs"],
    "golang": [".go"],
    "go": [".go"],
    "python": [".py", ".pyi"],
    "java": [".java"],
    "kotlin": [".kt", ".kts"],
    "csharp": [".cs"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h"],
    "c": [".c", ".h"],
    "ruby": [".rb"],
    "php": [".php"],
    "swift": [".swift"],
    "dart": [".dart"],
    "elixir": [".ex", ".exs"],
    "scala": [".scala"],
}
DEFAULT_IGNORE_SEGMENTS = [
    "node_modules", "target", "dist", "build", "vendor", "__pycache__", ".venv", "venv", "testdata",
]


def _normalize_dir(value: str) -> str:
    return (value or "").strip().strip("/")


@dataclass
class ParityConfig:
    """All ``[pr_parity]`` settings, with defaults matching ``configuration.toml``."""

    enabled: bool = True
    root: str = "src"
    languages: list[str] = field(default_factory=lambda: list(DEFAULT_LANGUAGES))
    auto_detect_languages: bool = True
    shared_dir: str = "src/shared"
    max_candidates_per_language: int = 5
    max_candidate_content_fetches: int = 3
    ignore_path_segments: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_SEGMENTS))
    use_llm: bool = True
    check_performance: bool = True
    check_parallelism: bool = True
    check_language_fit: bool = True
    check_distribution: bool = True
    service_dir_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_SERVICE_DIR_PATTERNS))
    publish_when_nothing_to_report: bool = False
    persistent_comment: bool = True
    extra_instructions: str = ""

    FIELDS = (
        "enabled", "root", "languages", "auto_detect_languages", "shared_dir",
        "max_candidates_per_language", "max_candidate_content_fetches", "ignore_path_segments",
        "use_llm", "check_performance", "check_parallelism", "check_language_fit", "check_distribution",
        "service_dir_patterns", "publish_when_nothing_to_report", "persistent_comment", "extra_instructions",
    )

    def __post_init__(self):
        self.root = _normalize_dir(self.root)
        self.shared_dir = _normalize_dir(self.shared_dir)
        self.languages = [lang.strip().lower() for lang in (self.languages or []) if str(lang).strip()]
        self.max_candidates_per_language = max(1, int(self.max_candidates_per_language))
        self.max_candidate_content_fetches = max(0, int(self.max_candidate_content_fetches))

    @classmethod
    def from_settings(cls, settings: Any = None) -> "ParityConfig":
        """Read ``[pr_parity]`` key by key (explicit reads keep the dead-key guard honest)."""
        settings = settings if settings is not None else get_settings()
        defaults = cls()
        values = {
            "enabled": settings.pr_parity.get("enabled", defaults.enabled),
            "root": settings.pr_parity.get("root", defaults.root),
            "languages": settings.pr_parity.get("languages", defaults.languages),
            "auto_detect_languages": settings.pr_parity.get("auto_detect_languages", defaults.auto_detect_languages),
            "shared_dir": settings.pr_parity.get("shared_dir", defaults.shared_dir),
            "max_candidates_per_language": settings.pr_parity.get("max_candidates_per_language",
                                                       defaults.max_candidates_per_language),
            "max_candidate_content_fetches": settings.pr_parity.get("max_candidate_content_fetches",
                                                         defaults.max_candidate_content_fetches),
            "ignore_path_segments": settings.pr_parity.get("ignore_path_segments", defaults.ignore_path_segments),
            "use_llm": settings.pr_parity.get("use_llm", defaults.use_llm),
            "check_performance": settings.pr_parity.get("check_performance", defaults.check_performance),
            "check_parallelism": settings.pr_parity.get("check_parallelism", defaults.check_parallelism),
            "check_language_fit": settings.pr_parity.get("check_language_fit", defaults.check_language_fit),
            "check_distribution": settings.pr_parity.get("check_distribution", defaults.check_distribution),
            "service_dir_patterns": settings.pr_parity.get("service_dir_patterns", defaults.service_dir_patterns),
            "publish_when_nothing_to_report": settings.pr_parity.get("publish_when_nothing_to_report",
                                                          defaults.publish_when_nothing_to_report),
            "persistent_comment": settings.pr_parity.get("persistent_comment", defaults.persistent_comment),
            "extra_instructions": settings.pr_parity.get("extra_instructions", defaults.extra_instructions),
        }
        assert set(values) == set(cls.FIELDS), "ParityConfig.FIELDS and from_settings() disagree"
        return cls(**{k: (list(v) if isinstance(v, (list, tuple)) else v) for k, v in values.items()})

    def to_dict(self) -> dict[str, Any]:
        """Flat, JSON-serialisable form (what a dashboard would round-trip)."""
        return {name: getattr(self, name) for name in self.FIELDS}

    def extensions_for(self, language: str) -> list[str]:
        return DEFAULT_LANGUAGE_EXTENSIONS.get(language.lower(), [])

    def any_language_extensions(self) -> set[str]:
        exts: set[str] = set()
        for lang in self.languages:
            exts.update(self.extensions_for(lang))
        return exts
