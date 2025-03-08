import threading
import time
from logging import getLogger
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.generate_result import (
    generate_astrology_result,
    prepare_for_astrology,
    result_to_voice,
)
from app.application.store_livechat import start_saving_livechat_message
from app.core.const import PG_URL
from app.infrastructure.repositoriesImpl import (
    WesternAstrologyResultRepositoryImpl,
    YoutubeLiveChatMessageRepositoryImpl,
)

logger = getLogger(__name__)
engine = create_engine(PG_URL, echo=False)


# --- スレッド・停止用イベントを管理するグローバル変数 ---
# スレッドの数分だけ辞書で管理する
threads: dict[str, Optional[threading.Thread]] = {
    "livechat": None,
    "result": None,
    "voice": None,
}
stop_events: dict[str, Optional[threading.Event]] = {
    "livechat": None,
    "result": None,
    "voice": None,
}


# --- 各処理を停止可能な形にラップする ---
def saving_livechat_message_thread(yt_video_id: str, stop_event: threading.Event):
    """
    ライブチャットの保存処理（無限ループ）
    """
    livechat_repo = YoutubeLiveChatMessageRepositoryImpl(session=Session(bind=engine))
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    logger.info("Start thread for saving livechat messages.")
    while not stop_event.is_set():
        try:
            start_saving_livechat_message(
                video_id=yt_video_id,
                livechat_repo=livechat_repo,
                astrology_repo=astrology_repo,
                stop_event=stop_event,  # 例：内部でチェックするための引数として渡す
            )
        except Exception as e:
            logger.exception("Failed to save live chat messages: " + str(e))
        # 万一内部処理がブロックしても、一定時間ごとに停止フラグをチェックするために sleep する
        time.sleep(1)
    logger.info("Stopped Thread for saving livechat messages.")


def generate_result_thread(stop_event: threading.Event):
    """占星術結果生成の無限ループ処理"""
    livechat_repo = YoutubeLiveChatMessageRepositoryImpl(session=Session(bind=engine))
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    logger.info("Start Thread for generating result.")
    while not stop_event.is_set():
        try:
            # 占いの準備
            prepare_for_astrology(astrology_repo, livechat_repo)
            # 占い結果の生成
            generate_astrology_result(astrology_repo)
            # 停止フラグのチェック間隔として sleep
            time.sleep(1)
        except Exception as e:
            logger.exception("Failed to generate result: " + str(e))
    logger.info("Stopped Thread for generating result.")


def generate_voice_thread(stop_event: threading.Event):
    """占星術結果を音声変換する無限ループ処理"""
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    logger.info("Start Thread for generating voice audio.")
    while not stop_event.is_set():
        try:
            result_to_voice(astrology_repo)
            time.sleep(0.1)
        except Exception as e:
            logger.exception("Failed to generate voice audio: " + str(e))
    logger.info("Stopped Thread for generating voice audio.")


# --- 各処理の開始／停止用関数 ---
def start_livechat(yt_video_id: str):
    """ライブチャット保存処理のスレッドを開始"""
    if not yt_video_id:
        return "YouTube動画IDが入力されていません。"
    global threads, stop_events
    if threads["livechat"] is None or not threads["livechat"].is_alive():
        stop_events["livechat"] = threading.Event()
        threads["livechat"] = threading.Thread(
            target=saving_livechat_message_thread,
            kwargs={"yt_video_id": yt_video_id, "stop_event": stop_events["livechat"]},
            name="LivechatThread",
        )
        threads["livechat"].start()
        return "開始しました"
    else:
        return "実行中です"


def stop_livechat():
    """ライブチャット保存処理のスレッドを停止"""
    global threads, stop_events
    if threads["livechat"] is not None and threads["livechat"].is_alive():
        stop_events[
            "livechat"
        ].set()  # 無限ループ内でイベントをチェックしているため停止可能
        threads["livechat"].join(timeout=2)
        threads["livechat"] = None
        return "停止しました"
    else:
        return "動作していません"


def start_result():
    """結果生成処理のスレッドを開始"""
    global threads, stop_events
    if threads["result"] is None or not threads["result"].is_alive():
        stop_events["result"] = threading.Event()
        threads["result"] = threading.Thread(
            target=generate_result_thread,
            kwargs={"stop_event": stop_events["result"]},
            name="ResultThread",
        )
        threads["result"].start()
        return "開始しました"
    else:
        return "既に実行中です"


def stop_result():
    """結果生成処理のスレッドを停止"""
    global threads, stop_events
    if threads["result"] is not None and threads["result"].is_alive():
        stop_events["result"].set()
        threads["result"].join(timeout=2)
        threads["result"] = None
        return "停止しました"
    else:
        return "動作していません"


def start_voice_generate():
    """音声生成処理のスレッドを開始"""
    global threads, stop_events
    if threads["voice"] is None or not threads["voice"].is_alive():
        stop_events["voice"] = threading.Event()
        threads["voice"] = threading.Thread(
            target=generate_voice_thread,
            kwargs={"stop_event": stop_events["voice"]},
            name="VoiceThread",
        )
        threads["voice"].start()
        return "開始しました"
    else:
        return "既に実行中です"


def stop_voice_generate():
    """音声生成処理のスレッドを停止"""
    global threads, stop_events
    if threads["voice"] is not None and threads["voice"].is_alive():
        stop_events["voice"].set()
        threads["voice"].join(timeout=2)
        threads["voice"] = None
        return "停止しました"
    else:
        return "動作していません"
