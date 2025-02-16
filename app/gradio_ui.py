# isort: off
from app.core import logging_config  # これにより設定が適用される

# isort: on
import threading
import time
from enum import Enum
from logging import getLogger
from typing import Optional

import gradio as gr
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.audio import play_audio_file
from app.application.generate_result import (
    generate_astrology_result,
    get_astrology_results_for_view,
    prepare_for_astrology,
    result_to_voice,
)
from app.application.store_livechat import start_saving_livechat_message
from app.core.const import PG_URL, GRAFANA_URL
from app.domain.repositories import WesternAstrologyResultRepository
from app.domain.westernastrology import WesternAstrologyStatusEntity
from app.domain.youtube.live import LiveChatMessageEntity
from app.infrastructure.repositoriesImpl import (
    WesternAstrologyResultRepositoryImpl,
    YoutubeLiveChatMessageRepositoryImpl,
)

logging_config.configure_logging()
logger = getLogger(__name__)
engine = create_engine(PG_URL, echo=False)


# --- データ表示用のモデル ---
class AstrologyView(BaseModel):
    chat_message: LiveChatMessageEntity
    status: WesternAstrologyStatusEntity


def get_view_data() -> list[AstrologyView]:
    """
    画面表示用のオブジェクトのリストを取得する
    """
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    status_list, chat_message_list = get_astrology_results_for_view(astrology_repo)
    views = []
    for status, message in zip(status_list, chat_message_list, strict=True):
        view: AstrologyView = AstrologyView(chat_message=message, status=status)
        views.append(view)
    return views


def h1_tag(text: str) -> str:
    return f"<h1>{text}</h1>"

def h2_tag(text: str) -> str:
    return f"<h2>{text}</h2>"

def process_status_text(text: str) -> str:
    return f"<div style='text-align: center; font-size: 18px; font-weight: bold;'>{text}</div>"


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


# --- スレッド・停止用イベントを管理するグローバル変数 ---
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


# --- 各処理の開始／停止用関数 ---
def start_livechat(yt_video_id: str):
    """ライブチャット保存処理のスレッドを開始"""
    if not yt_video_id:
        return process_status_text("YouTube動画IDが入力されていません。")
    global threads, stop_events
    if threads["livechat"] is None or not threads["livechat"].is_alive():
        stop_events["livechat"] = threading.Event()
        threads["livechat"] = threading.Thread(
            target=save_youtube_livechat_messages_loop,
            kwargs={"yt_video_id": yt_video_id, "stop_event": stop_events["livechat"]},
            name="LivechatThread",
        )
        threads["livechat"].start()
        return process_status_text("開始しました")
    else:
        return process_status_text("実行中です")


def stop_livechat():
    """ライブチャット保存処理のスレッドを停止"""
    global threads, stop_events
    if threads["livechat"] is not None and threads["livechat"].is_alive():
        stop_events[
            "livechat"
        ].set()  # 無限ループ内でイベントをチェックしているため停止可能
        threads["livechat"].join(timeout=2)
        threads["livechat"] = None
        return process_status_text("停止しました")
    else:
        return process_status_text("動作していません")


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
        return process_status_text("開始しました")
    else:
        return process_status_text("既に実行中です")


def stop_result():
    """結果生成処理のスレッドを停止"""
    global threads, stop_events
    if threads["result"] is not None and threads["result"].is_alive():
        stop_events["result"].set()
        threads["result"].join(timeout=2)
        threads["result"] = None
        return process_status_text("停止しました")
    else:
        return process_status_text("動作していません")


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
        return process_status_text("開始しました")
    else:
        return process_status_text("既に実行中です")


def stop_voice_generate():
    """音声生成処理のスレッドを停止"""
    global threads, stop_events
    if threads["voice"] is not None and threads["voice"].is_alive():
        stop_events["voice"].set()
        threads["voice"].join(timeout=2)
        threads["voice"] = None
        return process_status_text("停止しました")
    else:
        return process_status_text("動作していません")


# ======= 以下、AstrologyView 表示用の UI ロジック =======

class ViewStatus:
    def __init__(self, current_index: int, views: list[AstrologyView]):
        self.is_playable = False


def get_info_html(current_index: int, views: list[AstrologyView]):
    """
    データの情報を表示する HTML を返す。
    リンク先は別のコンテナで立ち上げているGrafanaのダッシュボード
    """
    length = len(views)

    return f"""
<h3>データ No. {current_index + 1}/{length}</h3>
"""


def get_chat_html(view: AstrologyView):
    """
    AstrologyView のチャットメッセージを HTML に整形して返す。
    """
    return f"""
<div>
    <span>・from : {view.chat_message.authorDetails.displayName}  ({view.chat_message.snippet.publishedAt})</span></br>
    <span>・コメント : {view.chat_message.snippet.displayMessage}</span></br>
</div>
"""


def get_astrology_html(view: AstrologyView):
    """
    AstrologyView の占星術結果を HTML に整形して返す。
    """
    return f"<div>{view.status.result}</div>"


def update_view(current_index, views: list[AstrologyView]):
    """
    表示中の AstrologyView を更新して内容を返す。
    """
    views: list[AstrologyView] = get_view_data()
    if not views:
        return "データなし", "", "", current_index, views, ""
    if current_index >= len(views):
        current_index = 0
    view = views[current_index]
    info_html = get_info_html(current_index, views)
    chat_html = get_chat_html(view)
    astrology_html = get_astrology_html(view)
    play_button_name = get_play_button_name(current_index, views)
    return info_html, chat_html, astrology_html, current_index, views, play_button_name


def prev_view(current_index: int, view_list: list[AstrologyView]):
    """
    「前へ」ボタン：表示中の AstrologyView インデックスをひとつ戻して内容を返す。
    """
    if not view_list:
        return "データなし", "", "", current_index, ""
    current_index = (current_index - 1) % len(view_list)
    view = view_list[current_index]
    info_html = get_info_html(current_index, view_list)
    chat_html = get_chat_html(view)
    astrology_html = get_astrology_html(view)
    play_button_name = get_play_button_name(current_index, view_list)
    return info_html, chat_html, astrology_html, current_index, play_button_name


def next_view(current_index: int, view_list: list[AstrologyView]):
    """
    「次へ」ボタン：表示中の AstrologyView インデックスをひとつ進めて内容を返す。
    """
    if not view_list:
        return "データなし", "", "", current_index, ""
    current_index = (current_index + 1) % len(view_list)
    view = view_list[current_index]
    info_html = get_info_html(current_index, view_list)
    chat_html = get_chat_html(view)
    astrology_html = get_astrology_html(view)
    play_button_name = get_play_button_name(current_index, view_list)
    return info_html, chat_html, astrology_html, current_index, play_button_name


def play_current_audio(
    current_index,
    view_list: list[AstrologyView],
    astro_repo: WesternAstrologyResultRepository,
):
    """
    「再生」ボタン：現在表示中の AstrologyView の voice_path の .wav ファイルを再生する。
    """
    if not view_list:
        return
    view = view_list[current_index]
    # TODO 再生を非同期にする
    play_audio_file(view.status.result_voice_path)
    # 再生済みフラグを更新
    view.status.is_played = True
    astro_repo.save([view.status])


def play_current_audio_ui(current_index, view_list):
    """
    UI用のラッパー関数。
    再生処理後に update_view を呼び出して最新情報を反映する。
    """
    repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    play_current_audio(current_index, view_list, repo)
    # 再生後は最新の view_list を取得するため、update_view を呼び出す
    return update_view(current_index, view_list)


def get_play_button_name(current_index: int, view_list: list[AstrologyView]):
    """
    """
    status = view_list[current_index].status
    if status.result_voice_path and not status.is_played:
        msg = "再生(未)"
    elif status.result_voice_path and status.is_played:
        msg = "再生(済)"
    else:
        msg = "音声未生成"
    return gr.Button(msg, elem_classes=["custom-play-btn"])

custom_css = """
.custom-start-btn {
    background-color: #2196F3 !important;
    color: #FFFFFF !important;
}
.custom-stop-btn {
    background-color: #F44336 !important;
    color: #FFFFFF !important;
}
.custom-play-btn {
    background-color: #4CAF50 !important;
    color: #FFFFFF !important;
}
"""
with gr.Blocks(css=custom_css) as demo:
    gr.HTML(h1_tag("YouTube Live AI占い"))
    # 表示エリア（3つのパーツ）と内部状態（current_index, view_list）を管理
    update_btn = gr.Button("更新")
    info_html_component = gr.HTML(value="")
    _ = gr.HTML(value=h2_tag("コメント情報"))
    chat_html_component = gr.HTML(value="")
    _ = gr.HTML(value=h2_tag("占い結果"))
    astrology_html_component = gr.Markdown(value="")

    # 内部状態を保持するための hidden state
    state_index = gr.State(0)
    state_views = gr.State([])

    with gr.Row():
        btn_prev = gr.Button("前へ")
        btn_play = gr.Button(" ", elem_classes=["custom-play-btn"])
        btn_next = gr.Button("次へ")

        # 更新ボタン：DBから最新データを取得して表示を更新
        update_btn.click(
            fn=update_view,
            inputs=[state_index, state_views],
            outputs=[
                info_html_component,
                chat_html_component,
                astrology_html_component,
                state_index,
                state_views,
                btn_play
            ],
        )

    # 前へボタン：内部状態の current_index を更新して表示を切り替え
    btn_prev.click(
        fn=prev_view,
        inputs=[state_index, state_views],
        outputs=[
            info_html_component,
            chat_html_component,
            astrology_html_component,
            state_index,
            btn_play
        ],
    )

    # 次へボタン：内部状態の current_index を更新して表示を切り替え
    btn_next.click(
        fn=next_view,
        inputs=[state_index, state_views],
        outputs=[
            info_html_component,
            chat_html_component,
            astrology_html_component,
            state_index,
            btn_play
        ],
    )

    # 再生ボタン：音声再生後、最新状態を反映
    btn_play.click(
        fn=play_current_audio_ui,
        inputs=[state_index, state_views],
        outputs=[
            info_html_component,
            chat_html_component,
            astrology_html_component,
            state_index,
            state_views,
            btn_play
        ],
    )

    gr.Markdown("-------------------------")
    with gr.Row():
        gr.HTML(h2_tag("バックグラウンドの処理の管理"))
    gr.HTML(f"""<a href="{GRAFANA_URL}">Progress View </a>""")


    video_id_input = gr.Textbox(interactive=True, placeholder="YouTube動画IDを入力してください", show_label=False)
    with gr.Row():
        btn_livechat_start = gr.Button(
            "コメント取得 START", elem_classes=["custom-start-btn"]
        )
        livechat_status = gr.HTML(process_status_text("未開始"))
        btn_livechat_stop = gr.Button(
            "コメント取得 STOP", elem_classes=["custom-stop-btn"]
        )
    with gr.Row():
        btn_result_start = gr.Button(
            "占い生成 START", elem_classes=["custom-start-btn"]
        )
        result_status = gr.HTML(process_status_text("未開始"))
        btn_result_stop = gr.Button("占い生成 STOP", elem_classes=["custom-stop-btn"])
    with gr.Row():
        btn_voice_start = gr.Button("音声生成 START", elem_classes=["custom-start-btn"])
        voice_status = gr.HTML(process_status_text("未開始"))
        btn_voice_stop = gr.Button("音声生成 STOP", elem_classes=["custom-stop-btn"])

    # 各ボタンのクリック時に対応する関数を呼び出す
    btn_livechat_start.click(fn=start_livechat, inputs=[video_id_input], outputs=livechat_status)
    btn_livechat_stop.click(fn=stop_livechat, inputs=[], outputs=livechat_status)

    btn_result_start.click(fn=start_result, inputs=[], outputs=result_status)
    btn_result_stop.click(fn=stop_result, inputs=[], outputs=result_status)

    btn_voice_start.click(fn=start_voice_generate, inputs=[], outputs=voice_status)
    btn_voice_stop.click(fn=stop_voice_generate, inputs=[], outputs=voice_status)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)  # TODO IPやポートは設定に書く
