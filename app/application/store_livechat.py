import time
from logging import DEBUG, getLogger
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.application.filter_yt_comment import is_astrology_target
from app.core.const import GEMINI_API_KEY, get_dummy_live_chat_message, is_test
from app.domain.youtube.live import LiveChatMessageEntity
from app.infrastructure.external.youtube.helper import (
    convert_chat_messages,
    fetch_chat_messages,
    get_live_chat_id,
    get_youtube_service,
)
from app.infrastructure.repositoriesImpl import (
    WesternAstrologyResultRepositoryImpl,
    YoutubeLiveChatMessageRepositoryImpl,
)

POLLING_INTERVAL_DEFAULT: int = 5  # デフォルトのポーリング間隔（秒）
KEY_PREFIX = "livechat"

logger = getLogger(__name__)


# TODO テスト時にはこの関数をモックに差し替える
def extract_chat_from_response(response: Dict[str, Any]) -> List[LiveChatMessageEntity]:

    if is_test():
        items = [get_dummy_live_chat_message(str(uuid4())) for _ in range(2)]
    else:
        items: List[Dict[str, Any]] = response.get("items", [])
    return convert_chat_messages(items)


def start_saving_livechat_message(
    video_id: str,
    livechat_repo: YoutubeLiveChatMessageRepositoryImpl,
    astrology_repo: WesternAstrologyResultRepositoryImpl | None = None,
    stop_event=None,
) -> None:
    logger.info(f"Start saving livechat messages for video_id: {video_id}")
    youtube = get_youtube_service(GEMINI_API_KEY)
    live_chat_id = get_live_chat_id(youtube, video_id)

    if not live_chat_id:
        logger.info("ライブチャットIDが取得できませんでした。")
        return
    logger.info(f"取得した liveChatId: {live_chat_id}")

    next_page_token: Optional[str] = None
    chat_count = 0

    try:
        while True:
            if stop_event and stop_event.is_set():
                break
            chat_response: Dict[str, Any] = fetch_chat_messages(
                youtube, live_chat_id, next_page_token
            )
            if not chat_response:
                logger.info("チャットレスポンスが空です。終了します。")
                break

            chat_list: list[LiveChatMessageEntity] = extract_chat_from_response(
                chat_response
            )

            # チャットメッセージを保存
            livechat_repo.save(chat_list)
            if logger.level == DEBUG:
                for chat in chat_list:
                    logger.debug(f"chat: {chat}")
                    who = chat.authorDetails.displayName
                    content = None
                    if chat.snippet.hasDisplayContent:
                        content = chat.snippet.displayMessage
                    logger.debug(f"chat saved: {who} - {content}")

            # 占い対象の時は、占いの対象か判断して保存
            if astrology_repo:
                chat_ids: list[str] = [chat.id for chat in chat_list]
                is_target_list: list[bool] = is_astrology_target(chat_list)
                astrology_repo.add_initial(chat_ids, is_target_list)

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
    finally:
        logger.info(f"取得したデータ数: {chat_count}")


if __name__ == "__main__":

    from app.core import logging_config  # これにより設定が適用される

    logging_config.configure_logging()

    from logging import getLogger

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.const import PG_URL
    from app.infrastructure.repositoriesImpl import (
        WesternAstrologyResultRepositoryImpl,
        YoutubeLiveChatMessageRepositoryImpl,
    )

    engine = create_engine(PG_URL, echo=True)
    livechat_repo = YoutubeLiveChatMessageRepositoryImpl(session=Session(bind=engine))
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    start_saving_livechat_message(
        video_id="f-qyvo2VU-8",
        livechat_repo=livechat_repo,
        astrology_repo=astrology_repo,
    )

    # generate_result_loop()
    # generate_voice_loop()
