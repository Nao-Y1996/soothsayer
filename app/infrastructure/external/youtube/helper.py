import csv
from logging import getLogger
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
from pydantic import ValidationError

from app.domain.youtube.live import LiveChatMessageEntity

logger = getLogger(__name__)


def get_youtube_service(api_key: str) -> Any:
    """
    YouTube Data APIクライアントを初期化して返却します。
    """
    return build("youtube", "v3", developerKey=api_key)


def get_live_chat_id(youtube: Any, video_id: str) -> Optional[str]:
    """
    指定した動画IDからライブチャットIDを取得します。
    ライブチャットが存在しない場合はNoneを返します。
    """
    try:
        video_response: Dict[str, Any] = (
            youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
        )
    except HttpError as e:
        logger.warning(f"Failed to fetch video info: {e}")
        return None

    items: List[Dict[str, Any]] = video_response.get("items", [])
    if not items:
        logger.warning(
            f"Could not find video with id: {video_id}, response: {video_response}"
        )
        return None

    live_details: Dict[str, Any] = items[0].get("liveStreamingDetails", {})
    return live_details.get("activeLiveChatId")


def fetch_chat_messages(
    youtube: Any, live_chat_id: str, page_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    指定したliveChatIdおよびページトークンを用いてチャットメッセージを取得します。
    """
    try:
        response: Dict[str, Any] = (
            youtube.liveChatMessages()
            .list(
                liveChatId=live_chat_id,
                part="snippet,authorDetails",
                pageToken=page_token,
            )
            .execute()
        )
        return response
    except HttpError as e:
        logger.warning(f"Failed to fetch chat messages: {e}")
        return {}


def convert_chat_messages(items: List[Dict[str, Any]]) -> List[LiveChatMessageEntity]:
    """
    APIレスポンスからLiveChatMessageのリストを作成。
    """
    messages = []
    for item in items:
        try:
            message = LiveChatMessageEntity.model_validate(item)
            messages.append(message)
        except ValidationError as e:
            logger.warning(
                f"Failed to parse livechat message to LiveChatMessageEntity: {e}"
            )
            continue
    return messages


def add_messages_to_csv(csv_path: str, messages: List[LiveChatMessageEntity]) -> None:
    """
    メッセージをCSVに追記します。
    """
    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        for message in messages:
            writer.writerow(message.to_csv_row())
