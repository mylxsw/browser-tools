import logging
import os

from dotenv import load_dotenv
from browser.util.singleton import singleton


@singleton
class Config:

    def __init__(self):
        logging.debug("loading configuration ...")
        load_dotenv(override=True)

    @property
    def debug(self) -> bool:
        return os.getenv("BROWSER_TOOLS_DEBUG", "false").lower() == "true"

    @property
    def verbose(self) -> bool:
        return (
            self.debug and os.getenv("BROWSER_TOOLS_VERBOSE", "false").lower() == "true"
        )

    @property
    def log_json_mode(self) -> bool:
        return os.getenv("BROWSER_TOOLS_LOG_JSON_MODE", "true").lower() == "true"

    @property
    def enable_cors(self) -> bool:
        return os.getenv("BROWSER_TOOLS_CORS_ENABLED", "false").lower() == "true"

    @property
    def zerox_model(self) -> str:
        return os.getenv("BROWSER_TOOLS_ZEROX_MODEL", "gpt-4o-mini")

    @property
    def temp_path(self) -> str:
        return os.getenv("BROWSER_TOOLS_TEMP_PATH", "/tmp/browser-tools").rstrip("/")