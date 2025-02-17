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
from app.interfaces.gradio_app.constract_html import div_center_bold_text

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
def save_youtube_livechat_messages_loop(yt_video_id: str, stop_event: threading.Event):
    """
    ライブチャットの保存処理（無限ループ）
    """
    livechat_repo = YoutubeLiveChatMessageRepositoryImpl(session=Session(bind=engine))
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    logger.info("start loop for saving livechat messages.")
    while not stop_event.is_set():
        try:
            start_saving_livechat_message(
                video_id=yt_video_id,
                livechat_repo=livechat_repo,
                astrology_repo=astrology_repo,
                stop_event=stop_event,  # 例：内部でチェックするための引数として渡す
            )
        except Exception as e:
            logger.error("Error in livechat saving loop: " + str(e))
        # 万一内部処理がブロックしても、一定時間ごとに停止フラグをチェックするために sleep する
        time.sleep(1)
    logger.info("Livechat saving loop terminated.")


def generate_result_loop(stop_event: threading.Event):
    """占星術結果生成の無限ループ処理"""
    livechat_repo = YoutubeLiveChatMessageRepositoryImpl(session=Session(bind=engine))
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    while not stop_event.is_set():
        # 占いの準備
        prepare_for_astrology(astrology_repo, livechat_repo)
        # 占い結果の生成
        generate_astrology_result(astrology_repo)
        # 停止フラグのチェック間隔として sleep
        time.sleep(5)
    logger.info("Result generation loop terminated.")


def generate_voice_loop(stop_event: threading.Event):
    """占星術結果を音声変換する無限ループ処理"""
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    while not stop_event.is_set():
        result_to_voice(astrology_repo)
        time.sleep(0.1)
    logger.info("Voice generation loop terminated.")


# --- 各処理の開始／停止用関数 ---
def start_livechat(yt_video_id: str):
    """ライブチャット保存処理のスレッドを開始"""
    if not yt_video_id:
        return div_center_bold_text("YouTube動画IDが入力されていません。")
    global threads, stop_events
    if threads["livechat"] is None or not threads["livechat"].is_alive():
        stop_events["livechat"] = threading.Event()
        threads["livechat"] = threading.Thread(
            target=save_youtube_livechat_messages_loop,
            kwargs={"yt_video_id": yt_video_id, "stop_event": stop_events["livechat"]},
            name="LivechatThread",
        )
        threads["livechat"].start()
        return div_center_bold_text("開始しました")
    else:
        return div_center_bold_text("実行中です")


def stop_livechat():
    """ライブチャット保存処理のスレッドを停止"""
    global threads, stop_events
    if threads["livechat"] is not None and threads["livechat"].is_alive():
        stop_events[
            "livechat"
        ].set()  # 無限ループ内でイベントをチェックしているため停止可能
        threads["livechat"].join(timeout=2)
        threads["livechat"] = None
        return div_center_bold_text("停止しました")
    else:
        return div_center_bold_text("動作していません")


def start_result():
    """結果生成処理のスレッドを開始"""
    global threads, stop_events
    if threads["result"] is None or not threads["result"].is_alive():
        stop_events["result"] = threading.Event()
        threads["result"] = threading.Thread(
            target=generate_result_loop,
            kwargs={"stop_event": stop_events["result"]},
            name="ResultThread",
        )
        threads["result"].start()
        return div_center_bold_text("開始しました")
    else:
        return div_center_bold_text("既に実行中です")


def stop_result():
    """結果生成処理のスレッドを停止"""
    global threads, stop_events
    if threads["result"] is not None and threads["result"].is_alive():
        stop_events["result"].set()
        threads["result"].join(timeout=2)
        threads["result"] = None
        return div_center_bold_text("停止しました")
    else:
        return div_center_bold_text("動作していません")


def start_voice_generate():
    """音声生成処理のスレッドを開始"""
    global threads, stop_events
    if threads["voice"] is None or not threads["voice"].is_alive():
        stop_events["voice"] = threading.Event()
        threads["voice"] = threading.Thread(
            target=generate_voice_loop,
            kwargs={"stop_event": stop_events["voice"]},
            name="VoiceThread",
        )
        threads["voice"].start()
        return div_center_bold_text("開始しました")
    else:
        return div_center_bold_text("既に実行中です")


def stop_voice_generate():
    """音声生成処理のスレッドを停止"""
    global threads, stop_events
    if threads["voice"] is not None and threads["voice"].is_alive():
        stop_events["voice"].set()
        threads["voice"].join(timeout=2)
        threads["voice"] = None
        return div_center_bold_text("停止しました")
    else:
        return div_center_bold_text("動作していません")
