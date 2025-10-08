import logging
import sys

import asgi_correlation_id

from browser.core.config import Config
from browser.util.singleton import singleton

def init_global():
    """
    Initialize global configuration
    """
    sys.excepthook = global_exception_handler


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Global exception handler
    """
    if exc_type == KeyboardInterrupt:
        sys.exit(1)

    logging.error(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def init_logger(level=None, json_mode=None):
    """
    Initialize the logger
    """
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.addFilter(asgi_correlation_id.CorrelationIdFilter())
    if json_mode:
        from pythonjsonlogger import jsonlogger

        formatter = jsonlogger.JsonFormatter(
            "[%(correlation_id)s] %(message)%(levelno)s%(levelname)%(name)%(created)f%(asctime)%(lineno)d%(pathname)s%(funcName)s"
        )
        ch.setFormatter(formatter)
    else:
        import colorlog

        formatter = colorlog.ColoredFormatter(
            "%(asctime)s - %(log_color)s%(levelname)s%(reset)s - [%(correlation_id)s] %(module)s/%(funcName)s:%(lineno)d - %(message)s",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            style="%",
        )
        ch.setFormatter(formatter)

    logging.basicConfig(level=level, handlers=[ch], force=True)
    # disable uvicorn access log
    logging.getLogger("uvicorn.access").disabled = True

@singleton
class Infra:

    def __init__(self):
        self.__config = Config()

    @property
    def config(self) -> Config:
        return self.__config
