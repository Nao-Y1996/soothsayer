import time
from logging import DEBUG, getLogger
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.application.filter_yt_comment import filter_astrology_target
from app.application.thread_manager import ThreadTask
from app.core.const import get_dummy_live_chat_message, is_test
from app.domain.repositories import (
    WesternAstrologyStateRepository,
    YoutubeLiveChatMessageRepository,
)
from app.domain.westernastrology import WesternAstrologyStateEntity
from app.domain.youtube.live import LiveChatMessageEntity
from app.infrastructure.external.youtube.helper import (
    convert_chat_messages,
    fetch_chat_messages,
    get_live_chat_id,
    get_youtube_service,
)

POLLING_INTERVAL_DEFAULT: int = 5  # デフォルトのポーリング間隔（秒）

logger = getLogger(__name__)


# TODO テスト時にはこの関数をモックに差し替える
def extract_chat_from_response(response: Dict[str, Any]) -> List[LiveChatMessageEntity]:
    if is_test():
        items = [get_dummy_live_chat_message(str(uuid4())) for _ in range(2)]
    else:
        items: List[Dict[str, Any]] = response.get("items", [])
    return convert_chat_messages(items)


class LivechatTask(ThreadTask):

    def __init__(
        self,
        name: str,
        western_astrology_repo: WesternAstrologyStateRepository,
        livechat_repo: YoutubeLiveChatMessageRepository,
    ):
        super().__init__(name)
        self.western_astrology_repo = western_astrology_repo
        self.livechat_repo = livechat_repo
        self.live_chat_id = None

    def start(self) -> str:
        if not self.live_chat_id:
            logger.warning("Live chat id is not set.")
            return "LiveChat IDが取得できません"
        return super().start()

    def stop(self) -> str:
        self.live_chat_id = None
        return super().stop()

    def set_live_chat_id(self, yt_video_id: str):

        youtube = get_youtube_service()
        live_chat_id = get_live_chat_id(youtube, yt_video_id)

        if not live_chat_id:
            logger.warning(f"failed to get live chat id from video id {yt_video_id}")
        else:
            self.live_chat_id = live_chat_id
            logger.info(
                f"Successfully fetched liveChatId: {live_chat_id} from video id {yt_video_id}"
            )

    def run(self):
        """
        ライブチャットの保存処理（無限ループ）
        """
        logger.info(
            f"Start thread for saving livechat messages. live_chat_id: {self.live_chat_id}"
        )
        youtube = get_youtube_service()

        next_page_token: Optional[str] = None
        while not self.stop_event.is_set():
            try:
                chat_response: Dict[str, Any] = fetch_chat_messages(
                    youtube, self.live_chat_id, next_page_token
                )
                if not chat_response:
                    logger.info("チャットレスポンスが空です。終了します。")
                    break

                chat_list: list[LiveChatMessageEntity] = extract_chat_from_response(
                    chat_response
                )

                # チャットメッセージを保存
                self.livechat_repo.save(chat_list)
                if logger.level == DEBUG:
                    for chat in chat_list:
                        logger.debug(f"chat: {chat}")
                        who = chat.authorDetails.displayName
                        content = None
                        if chat.snippet.hasDisplayContent:
                            content = chat.snippet.displayMessage
                        logger.debug(f"chat saved: {who} - {content}")

                # 占い対象の時は、占いの対象か判断して保存
                if self.western_astrology_repo:  # FIXME: 意味のなさそうなif文
                    target_chat_list: list[LiveChatMessageEntity] = (
                        filter_astrology_target(chat_list)
                    )
                    western_astrology_targets: list[WesternAstrologyStateEntity] = []
                    for chat in target_chat_list:
                        western_astrology_targets.append(
                            WesternAstrologyStateEntity.get_initial(
                                message_id=chat.id,
                                is_target=True,
                            )
                        )
                    self.western_astrology_repo.save(western_astrology_targets)

                next_page_token = chat_response.get("nextPageToken")
                if not next_page_token:
                    logger.info("すべてのメッセージを取得しました。")
                    break

                polling_interval_ms = chat_response.get("pollingIntervalMillis")
                polling_interval: float = (
                    (int(polling_interval_ms) / 1000.0)
                    if polling_interval_ms
                    else POLLING_INTERVAL_DEFAULT
                )

                time.sleep(polling_interval)

            except Exception as e:
                logger.exception("Failed to save live chat messages: " + str(e))
            # 万一内部処理がブロックしても、一定時間ごとに停止フラグをチェックするために sleep する
            time.sleep(1)
        logger.info("Stopped Thread for saving livechat messages.")
