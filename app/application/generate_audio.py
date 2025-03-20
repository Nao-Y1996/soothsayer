import time
from logging import getLogger

from app.application.audio import txt_to_audiofile
from app.application.thread_manager import ThreadTask
from app.core.const import AUDIO_DIR
from app.domain.repositories import WesternAstrologyStateRepository
from app.domain.westernastrology import WesternAstrologyStateEntity
from app.infrastructure.external.stylebertvit2.voice import is_alive

logger = getLogger(__name__)


def result_to_voice(astrology_repo: WesternAstrologyStateRepository) -> None:
    """
    占い結果を音声化し、DBに保存する
    """
    # まだ音声化されていない占星術ステータスを取得
    target_astrology_state_list: list[WesternAstrologyStateEntity] = (
        astrology_repo.get_no_voice_target(limit=1)
    )  # TODO limitは設定で変えるようにする
    if not target_astrology_state_list:
        return

    # 占い結果を音声化
    logger.info("Start generating voice for astrology result list.")
    for astrology_state in target_astrology_state_list:
        result = astrology_state.result

        logger.info(
            f"Start generating voice for astrology result: (message_id={astrology_state.message_id})"
        )
        if result:
            # 音声化
            try:
                audio_file_path = txt_to_audiofile(
                    text=result,
                    audiofile_path=AUDIO_DIR / f"{astrology_state.message_id}.wav",
                )
                astrology_state.result_voice_path = audio_file_path
                logger.info(
                    f"Succeeded to generate voice for astrology result: (message_id={astrology_state.message_id})"
                )
                # 音声化結果を保存
                # 生成は1つ1つが時間がかかるので、1つの結果を生成したらすぐに保存する
                astrology_repo.save([astrology_state])
            except IOError as e:
                logger.exception(
                    f"Failed to generate voice for astrology result: (message_id={astrology_state.message_id})"
                )
                raise e
        else:
            # get_no_voice_targetで結果が空ではないものを取得しているので、ここに来ることはないはず
            logger.exception(
                f"No result to generate voice: (message_id={astrology_state.message_id})"
            )


class VoiceTask(ThreadTask):

    def __init__(
        self, name: str, western_astrology_repo: WesternAstrologyStateRepository
    ):
        super().__init__(name)
        self.western_astrology_repo = western_astrology_repo

    def start(self) -> str:
        if not is_alive():
            logger.warning("Voice model is not alive.")
            return "音声モデルの起動を確認してください"
        return super().start()

    def run(self):
        """占星術結果を音声変換する無限ループ処理"""
        logger.info("Start Thread for generating voice audio.")
        while not self.stop_event.is_set():
            try:
                result_to_voice(self.western_astrology_repo)
                time.sleep(0.1)
            except Exception as e:
                logger.exception("Failed to generate voice audio: " + str(e))
        logger.info("Stopped Thread for generating voice audio.")
