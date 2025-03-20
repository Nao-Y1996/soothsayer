from app.application.thread_manager import ThreadTask
from app.domain.repositories import WesternAstrologyStateRepository
from app.interfaces.obs.utils import update_waiting_display
from logging import getLogger
import time

logger = getLogger(__name__)


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
        logger.info("Start Thread for generating result.")
        while not self.stop_event.is_set():
            count = len(self.state_repo.get_waiting_audio_play_state())

            display_content = self.display_format.format(count)
            update_waiting_display(display_content)

            logger.info(f"Successfully updated display: {display_content}")
            time.sleep(self.interval)
        logger.info("StateDisplayTreadTask is stopped.")
