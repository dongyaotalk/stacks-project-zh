from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK_FILE = PROJECT_ROOT / "upstream.lock"
DEFAULT_TRANSLATION_DATA = PROJECT_ROOT / "translation-data"
DEFAULT_RENDER_ROOT = PROJECT_ROOT / "springer-template" / "translations"
PACKAGE_NAME = "stacks_zh"
