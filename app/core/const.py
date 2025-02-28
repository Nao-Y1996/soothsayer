import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import URL

from app import config

# プロジェクトルートのパス
ROOT = Path(__file__).resolve().parent.parent.parent


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
def get_current_time_formatted() -> str:
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


sample_names = [
    "たけし",
    "さくら",
    "しんじ",
    "みか",
    "ひろし",
    "あや",
    "けんた",
    "ゆかり",
]
sample_messages = [
    "【占い依頼】1985/6/12 午前10時 大阪生まれです",
    "占い依頼をお願いします！1995年9月21日、15時30分、名古屋生まれです",
    "占い依頼です。2000/5/5 午後6時 福岡生まれです",
    "【占い依頼】1978年11月30日、朝7時45分、札幌生まれ。",
    "占い依頼！1992/3/18 23時 神戸生まれです。",
    "【占い依頼】2005年8月8日 午前2時 京都生まれです！",
    "占い依頼です。1989年4月27日、夜10時半、仙台生まれです。",
    "【占い依頼】1997/12/14 18時45分 広島生まれです。",
    "占い依頼お願いします！2010年7月7日 午後3時 長崎生まれ。",
    "【占い依頼】1983年2月1日 深夜1時 東京生まれです。",
]


def get_dummy_live_chat_message(uuid: str) -> dict[str, Any]:
    return {
        "id": uuid,
        "etag": "Y94zk6_MVvjIEZWLP-nDIi6iPOs",
        "kind": "youtube#liveChatMessage",
        "snippet": {
            "type_": None,
            "liveChatId": "Cg0KC2M5UGhZcHp5ZlZzKicKGFVDR0NaQVlxNVh4b2psX3RTWGNWSmhpURILYzlQaFlwenlmVnM",
            "pollDetails": None,
            "publishedAt": get_current_time_formatted(),
            "displayMessage": random.choice(sample_messages),
            "authorChannelId": "UCJZLZ_W-Wo-HOshWEfoVyOA",
            "superChatDetails": None,
            "hasDisplayContent": True,
            "newSponsorDetails": None,
            "userBannedDetails": None,
            "textMessageDetails": {"messageText": random.choice(sample_messages)},
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
            "displayName": random.choice(sample_names),
            "isChatOwner": False,
            "isChatSponsor": False,
            "isChatModerator": False,
            "profileImageUrl": "https://yt3.ggpht.com/IQcjsi8SkZ966PFo79aUwbdQwLVI_i-18KH2wjp0kgDk5uPYAlYrUsWp_3CgyHDrrSfYELg1Lg=s88-c-k-c0x00ffffff-no-rj",
        },
    }


# app配下のディレクトリパスがDBに保存される
AUDIO_DIR = ROOT / "app" / config.audio_dir
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
