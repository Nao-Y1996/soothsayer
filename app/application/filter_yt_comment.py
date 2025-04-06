from logging import getLogger

from app.domain.youtube.live import LiveChatMessageEntity

logger = getLogger(__name__)


def filter_astrology_target(
    chat_list: list[LiveChatMessageEntity],
) -> list[LiveChatMessageEntity]:
    """
    チャットメッセージが占い対象かどうかを判定する。
    占い対象の場合はTrue、それ以外はFalseを返す。
    """
    result: list[LiveChatMessageEntity] = []
    for chat in chat_list:

        if chat is None:
            continue
        if chat.snippet is None:
            continue
        if chat.snippet.textMessageDetails is None:
            continue
        if chat.snippet.textMessageDetails.messageText is None:
            continue

        if "占い依頼" in chat.snippet.textMessageDetails.messageText:
            result.append(chat)

    return result
