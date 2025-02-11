# app/core/logging_config.py

from typing import Literal

from app.core.const import LOG_DIR

# -----------------------------------------------------------------------------
log_file_path = LOG_DIR / "application.log"
# -----------------------------------------------------------------------------


LEVEL: Literal["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"] = "INFO"


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detail": {
            "format": "%(asctime)s [%(levelname)s] %(module)s %(funcName)s:%(lineno)d - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detail",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "detail",
            "filename": str(log_file_path),  # 出力するログファイルのパス
            # 以下の設定は「秒」を単位とするため、30日間を秒数に変換
            "when": "S",  # 秒単位でのローテーションを行う指定
            "interval": 2592000,  # 30日分の秒数
            "backupCount": 12,  # 古いログファイルの保持数（例：直近12ヶ月分）
            "encoding": "utf8",
        },
    },
    "root": {
        "level": LEVEL,
        "handlers": ["console", "file"],
    },
}


def configure_logging():
    import logging.config

    logging.config.dictConfig(LOGGING_CONFIG)


# モジュールがimportされた時に設定を適用
# configure_logging()
