import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
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
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

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


# 緯度軽度のデータを読み込む
city_data_csv = ROOT / "app" / "core" / "location_data" / "city.csv"
prefecture_data_csv = ROOT / "app" / "core" / "location_data" / "prefecture.csv"
city_df = pd.read_csv(city_data_csv, encoding="utf-8", skipinitialspace=True)
prefecture_df = pd.read_csv(
    prefecture_data_csv, encoding="utf-8", skipinitialspace=True
)

CITY_LOCATION_MAP = {}
for i, row in city_df.iterrows():
    city = row.city
    CITY_LOCATION_MAP[city] = (row.latitude, row.longitude)
    if city.endswith("市"):
        CITY_LOCATION_MAP[city[:-1]] = (row.latitude, row.longitude)

PREFECTURE_LOCATION_MAP = {}
for i, row in prefecture_df.iterrows():
    prefecture = row.prefecture
    PREFECTURE_LOCATION_MAP[prefecture] = (row.latitude, row.longitude)

    if (
        prefecture.endswith("県")
        or prefecture.endswith("府")
        or prefecture.endswith("都")
    ):
        PREFECTURE_LOCATION_MAP[prefecture[:-1]] = (row.latitude, row.longitude)


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
    # 正常系
    "【占い依頼】1985/6/12 午前10時 大阪生まれです",
    "【占い依頼】1985/6/12 午前10時",
    "【占い依頼】1985/6/12 福岡生まれです",
    "【占い依頼】1985/6/12",
    "占い依頼をお願いします！1995年9月21日、15時30分、名古屋生まれです",
    "占い依頼をお願いします！1995年9月21日、15時30分",
    "占い依頼をお願いします！1995年9月21日、愛知生まれです",
    "占い依頼をお願いします！1995年9月21日",
    "占い依頼です。誕生日：2000/05/23 午後9時　生まれた場所：北海道",
    "占い依頼です。誕生日：2000/05/23 午後9時",
    "占い依頼です。誕生日：2000/05/23 生まれた場所：宮城",
    "占い依頼です。誕生日：2000/05/23 ",
    # 異常系
    "占い依頼です",
    "こんにちは、占い依頼お願いします",
    "こんにちは",
    "こんばんは",
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

    print(CITY_LOCATION_MAP)
