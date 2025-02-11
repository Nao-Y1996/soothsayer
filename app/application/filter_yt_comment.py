from logging import getLogger

from app.domain.youtube.live import LiveChatMessageEntity

logger = getLogger(__name__)


def is_astrology_target(chat_list: list[LiveChatMessageEntity]) -> list[bool]:
    """
    チャットメッセージが占い対象かどうかを判定する。
    占い対象の場合はTrue、それ以外はFalseを返す。
    """
    result = []
    for chat in chat_list:

        if chat is None:
            result.append(False)
            continue
        if chat.snippet is None:
            result.append(False)
            continue
        if chat.snippet.textMessageDetails is None:
            result.append(False)
            continue
        if chat.snippet.textMessageDetails.messageText is None:
            result.append(False)
            continue

        if "占い依頼" in chat.snippet.textMessageDetails.messageText:
            result.append(True)
        else:
            result.append(False)

    return result
