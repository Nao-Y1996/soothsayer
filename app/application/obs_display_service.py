import time
from logging import getLogger

from app.application.thread_manager import ThreadTask
from app.config import (
    COMMENT_FILE_PATH,
    OBS_SCENE_NAME,
    OBS_SOURCE_NAME_FOR_GROUP,
    RESULT_FILE_PATH,
    USER_NAME_FILE_PATH,
    WAITING_DISPLAY_FILE_PATH,
)
from app.domain.repositories import WesternAstrologyStateRepository
from app.infrastructure.external.obs.utils import (
    get_scene_item_id_by_name,
    set_scene_item_enabled,
)

logger = getLogger(__name__)


def toggle_visibility_user_info_in_obs(enable: bool):
    source_id_for_user_name = get_scene_item_id_by_name(
        OBS_SCENE_NAME, OBS_SOURCE_NAME_FOR_GROUP
    )
    set_scene_item_enabled(
        scene_name=OBS_SCENE_NAME, scene_item_id=source_id_for_user_name, enabled=enable
    )


def _update_file(file_path: str, content: str, log_field: str, error_msg: str) -> None:
    logger.info(f"{log_field}={content!r}")
    try:
        with open(file_path, mode="w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logger.exception(f"{error_msg}: {e}")
        raise


def _get_file_content(file_path: str, error_msg: str) -> str:
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.exception(f"{error_msg}: {e}")
        raise


def update_user_name(user_name: str) -> None:
    _update_file(
        file_path=USER_NAME_FILE_PATH,
        content=user_name,
        log_field="user_name",
        error_msg="Failed to update username",
    )


def update_comment(comment: str) -> None:
    _update_file(
        file_path=COMMENT_FILE_PATH,
        content=comment,
        log_field="comment",
        error_msg="Failed to update comment",
    )


def update_waiting_display(display_content: str) -> None:
    _update_file(
        file_path=WAITING_DISPLAY_FILE_PATH,
        content=display_content,
        log_field="display_content",
        error_msg="Failed to update waiting list",
    )


def update_result_to_show(result: str) -> None:
    _update_file(
        file_path=RESULT_FILE_PATH,
        content=result,
        log_field="result",
        error_msg="Failed to update result",
    )


def get_user_name() -> str:
    return _get_file_content(
        file_path=USER_NAME_FILE_PATH,
        error_msg="Failed to get username",
    )


def get_comment() -> str:
    return _get_file_content(
        file_path=COMMENT_FILE_PATH,
        error_msg="Failed to get comment",
    )


class DisplayWaitingCountTreadTask(ThreadTask):

    def __init__(
        self,
        name: str,
        state_repo: WesternAstrologyStateRepository,
        display_format: str = "占い待ち: {}人",
        interval: int = 5,
    ):
        super().__init__(name)
        self.state_repo = state_repo
        self.display_format = display_format
        self.interval = interval

    def run(self) -> None:
        logger.info("Start Thread for fetching waiting count.")
        while not self.stop_event.is_set():
            count = len(self.state_repo.get_waiting_audio_play_state())

            display_content = self.display_format.format(count)
            update_waiting_display(display_content)

            logger.info(f"Successfully updated display: {display_content}")
            time.sleep(self.interval)
        logger.info("StateDisplayTreadTask is stopped.")
