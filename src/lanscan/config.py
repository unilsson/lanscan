from dataclasses import dataclass
from pathlib import Path
import tomllib


class ConfigError(Exception):
    """Invalid or missing local lanscan configuration."""


@dataclass(frozen=True, slots=True)
class OpnsenseConfig:
    url: str
    api_key: str
    api_secret: str
    verify_tls: bool = True
    timeout: float = 3.0


def default_config_path() -> Path:
    return Path.home() / ".config" / "lanscan" / "config.toml"


def load_opnsense_config(path: Path | None = None) -> OpnsenseConfig:
    config_path = path or default_config_path()

    try:
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(
            f"configuration file not found: {config_path}"
        ) from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(
            f"could not read configuration file {config_path}: {exc}"
        ) from exc

    section = data.get("opnsense")
    if not isinstance(section, dict):
        raise ConfigError(
            f"missing [opnsense] section in {config_path}"
        )

    url = str(section.get("url", "")).strip().rstrip("/")
    api_key = str(section.get("api_key", "")).strip()
    api_secret = str(section.get("api_secret", "")).strip()

    if not url:
        raise ConfigError("missing opnsense.url")
    if not url.lower().startswith("https://"):
        raise ConfigError("opnsense.url must use https://")
    if not api_key:
        raise ConfigError("missing opnsense.api_key")
    if not api_secret:
        raise ConfigError("missing opnsense.api_secret")

    verify_tls = section.get("verify_tls", True)
    if not isinstance(verify_tls, bool):
        raise ConfigError("opnsense.verify_tls must be true or false")

    timeout = section.get("timeout", 3.0)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ConfigError("opnsense.timeout must be a number")
    timeout = float(timeout)
    if timeout <= 0:
        raise ConfigError("opnsense.timeout must be greater than 0")

    return OpnsenseConfig(
        url=url,
        api_key=api_key,
        api_secret=api_secret,
        verify_tls=verify_tls,
        timeout=timeout,
    )
