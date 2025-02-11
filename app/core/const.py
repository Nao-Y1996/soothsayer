import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import URL

from app import config

# プロジェクトルートのパス
ROOT = Path(__file__).parent.parent.parent


def is_test():
    return config.mode_type == "test"


load_dotenv(dotenv_path=ROOT / ".env", override=True)

# APIキー
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# PostgreSQL
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
PG_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    database=POSTGRES_DB,
    host=POSTGRES_HOST,
    port=int(POSTGRES_PORT),
).render_as_string(hide_password=False)


# テスト用のダミーデータ
def get_dummy_live_chat_message(uuid: str) -> dict[str, Any]:
    return {
        "id": uuid,
        "etag": "Y94zk6_MVvjIEZWLP-nDIi6iPOs",
        "kind": "youtube#liveChatMessage",
        "snippet": {
            "type_": None,
            "liveChatId": "Cg0KC2M5UGhZcHp5ZlZzKicKGFVDR0NaQVlxNVh4b2psX3RTWGNWSmhpURILYzlQaFlwenlmVnM",
            "pollDetails": None,
            "publishedAt": "2025-02-09 12:00:48",
            "displayMessage": config.dummy_message,
            "authorChannelId": "UCJZLZ_W-Wo-HOshWEfoVyOA",
            "superChatDetails": None,
            "hasDisplayContent": True,
            "newSponsorDetails": None,
            "userBannedDetails": None,
            "textMessageDetails": {"messageText": config.dummy_message},
            "superStickerDetails": None,
            "messageDeletedDetails": None,
            "fanFundingEventDetails": None,
            "membershipGiftingDetails": None,
            "memberMilestoneChatDetails": None,
            "giftMembershipReceivedDetails": None,
        },
        "authorDetails": {
            "channelId": "UCJZLZ_W-Wo-HOshWEfoVyOA",
            "channelUrl": "http://www.youtube.com/channel/UCJZLZ_W-Wo-HOshWEfoVyOA",
            "isVerified": False,
            "displayName": config.dummy_user_name,
            "isChatOwner": False,
            "isChatSponsor": False,
            "isChatModerator": False,
            "profileImageUrl": "https://yt3.ggpht.com/IQcjsi8SkZ966PFo79aUwbdQwLVI_i-18KH2wjp0kgDk5uPYAlYrUsWp_3CgyHDrrSfYELg1Lg=s88-c-k-c0x00ffffff-no-rj",
        },
    }


# appは以下のディレクトリパスがDBに保存される
AUDIO_DIR = ROOT / "app" / config.video_dir
# TODO 任意のパスでも動作するようにする
AUDIO_DIR.mkdir(exist_ok=True, parents=True)

LOG_DIR = ROOT / config.log_dir
LOG_DIR.mkdir(exist_ok=True, parents=True)

GRAFANA_URL = config.grafana_url

if __name__ == "__main__":
    print(f"ROOT: {ROOT}")
    print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
    print(f"GOOGLE_API_KEY: {GOOGLE_API_KEY}")
    print(f"GEMINI_API_KEY: {GEMINI_API_KEY}")
    print(f"POSTGRES_USER: {POSTGRES_USER}")
    print(f"POSTGRES_PASSWORD: {POSTGRES_PASSWORD}")
    print(f"POSTGRES_DB: {POSTGRES_DB}")
    print(f"POSTGRES_HOST: {POSTGRES_HOST}")
    print(f"POSTGRES_PORT: {POSTGRES_PORT}")
    print(f"PG_URL: {PG_URL}")
