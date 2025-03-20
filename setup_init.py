import functools
import logging
import os
import shutil
from datetime import datetime
from logging import StreamHandler, getLogger
from pathlib import Path

import requests

logger = getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

ROOT = Path(__file__).resolve().parent

NOW_STR = datetime.now().strftime("%Y%m%d_%H%M%S")


def download_content(url: str, save_dir: str, filename=None):
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = os.path.basename(url)
        if not filename:
            raise ValueError(
                "Filename cannot be determined from url. Please specify a filename."
            )

    file_path = Path(save_dir) / filename
    if file_path.exists():
        logger.info(f"File {file_path} already exists. Skipping download.")
        return
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Successfully downloaded from {url} to {file_path}")
        return file_path
    except requests.exceptions.RequestException as e:
        logger.exception(f"Failed to download from {url} to {file_path}")


def setup_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        _ = "=" * len(func_name)  # type: ignore
        logger.info(f"==== {func_name} ====")
        result = func(*args, **kwargs)
        logger.info(f"==== {_} ====\n")
        return result

    return wrapper


@setup_logging
def setup_config():
    config_sample = ROOT / "app" / "config_sample.py"
    config = ROOT / "app" / "config.py"
    if config.exists():
        backup_config = str(config).replace(".py", f"_backup_{NOW_STR}.py")
        shutil.copy(config_sample, backup_config)
        logger.info(f"config.py was copied to {backup_config.replace(str(ROOT), '')}")

    shutil.copyfile(str(config_sample), str(config))
    logger.info(f"config.py was created in {str(config).replace(str(ROOT), '')}")
    logger.info(f"【TODO】Please set your own config variables to {config}")


@setup_logging
def setup_ephemeris():
    urls = [
        "https://github.com/flatangle/flatlib/raw/master/flatlib/resources/swefiles/seas_18.se1",
        "https://github.com/flatangle/flatlib/raw/master/flatlib/resources/swefiles/semo_18.se1",
        "https://github.com/flatangle/flatlib/raw/master/flatlib/resources/swefiles/sepl_18.se1",
    ]
    save_dir = ROOT / "app/application/ephemeris"
    for url in urls:
        download_content(url, str(save_dir))


@setup_logging
def setup_env():
    dot_env_sample = ROOT / ".env.sample"
    dot_env = ROOT / ".env"
    if dot_env.exists():
        backup_env = str(dot_env).replace(".env", f".env.backup_{NOW_STR}")
        shutil.copy(dot_env, backup_env)
        logger.info(f".env was copied to {backup_env}")

    shutil.copy(str(dot_env_sample), str(dot_env))
    logger.info(f".env was created in {dot_env}")
    logger.info(f"【TODO】Please set your own env variables to {dot_env}")


@setup_logging
def setup_prompts():
    prompts_dir = ROOT / "app" / "application" / "prompts"
    sample_prompts = [
        "western_astrology.sample.md",
    ]
    for smple in sample_prompts:
        sample_prompt_file = prompts_dir / smple
        prompt_file = Path(str(sample_prompt_file).replace(".sample.md", ".md"))

        if prompt_file.exists():
            backup_prompt = str(prompt_file).replace(".md", f".backup_{NOW_STR}.md")
            shutil.copy(prompt_file, backup_prompt)
            logger.info(f"{prompt_file} was copied to {backup_prompt}")

        shutil.copy(str(sample_prompt_file), str(prompt_file))
        logger.info(f"{prompt_file} was created in {prompt_file}")
        logger.info(f"【TODO】Please set your prompt to {prompt_file}")


if __name__ == "__main__":
    setup_config()
    setup_ephemeris()
    setup_env()
    setup_prompts()
