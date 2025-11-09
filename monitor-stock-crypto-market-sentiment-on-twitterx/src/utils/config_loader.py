# PROJECT_ROOT -> .../monitor-stock-crypto-market-sentiment-on-twitterx
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in configuration file {path}: {exc}") from exc

def _resolve_config(primary: str, fallback: str) -> Path:
    primary_path = PROJECT_ROOT / "config" / primary
    fallback_path = PROJECT_ROOT / "config" / fallback

    if primary_path.exists():
        return primary_path
    if fallback_path.exists():
        logger.warning("Primary config %s not found, falling back to %s", primary_path, fallback_path)
        return fallback_path

    raise FileNotFoundError(f"Neither {primary_path} nor {fallback_path} could be found.")

def load_settings() -> Dict[str, Any]:
    """
    Load scraper settings from config/settings.json, falling back to
    config/settings.example.json if the primary file does not exist.
    """
    path = _resolve_config("settings.json", "settings.example.json")
    settings = _load_json(path)

    if not isinstance(settings, dict):
        raise ValueError(f"Settings file {path} must contain a JSON object.")

    return settings

def load_credentials() -> Dict[str, Any]:
    """
    Load credentials from config/credentials.json, falling back to
    config/credentials.template.json if the primary file does not exist.
    """
    path = _resolve_config("credentials.json", "credentials.template.json")
    credentials = _load_json(path)

    if not isinstance(credentials, dict):
        raise ValueError(f"Credentials file {path} must contain a JSON object.")

    return credentials