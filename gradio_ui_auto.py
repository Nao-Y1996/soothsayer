# isort: off
from app.core import logging_config  # これにより設定が適用される

# isort: on
import time
from logging import getLogger

import gradio as gr

from app.application.audio_auto_player import AutoAudioPlayer
from app.application.generate_audio import VoiceTask
from app.application.generate_result import GenerateResultTask
from app.application.obs_display_service import (
    DisplayWaitingCountTreadTask,
    get_comment,
    get_user_name,
    update_comment,
    update_result_to_show,
    update_user_name, update_waiting_display,
)
from app.application.store_livechat import LivechatTask
from app.application.text_service import extract_enclosed
from app.application.thread_manager import ThreadTask
from app.core.const import GRAFANA_URL
from app.domain.westernastrology import WesternAstrologyStateEntity
from app.domain.youtube.live import LiveChatMessageEntity
from app.infrastructure.db_common import initialize_db as init_db
from app.infrastructure.repositoriesImpl import (
    WesternAstrologyStateRepositoryImpl,
    YoutubeLiveChatMessageRepositoryImpl,
)
from app.interfaces.gradio_app.constract_html import (
    div_center_bold_text,
    h1_tag,
    h2_tag,
)
from app.interfaces.obs.ui import (
    custom_css,
    get_user_name_and_comment_html,
)


def initialize_db():
    try:
        init_db()
        update_user_name("")
        update_comment("")
        update_result_to_show("")
        update_waiting_display("")
        gr.Info("データベースを初期化しました.", duration=3)
    except Exception as e:
        raise gr.Error(f"データベースの初期化に失敗しました. {e}", duration=3)


def update_user_info_in_obs(
    state: WesternAstrologyStateEntity, chat_message: LiveChatMessageEntity
):
    """
    OBSに表示する情報を更新して返す
    """
    user_name = chat_message.authorDetails.displayName
    comment = chat_message.snippet.displayMessage

    # 占い結果から<< >> で囲まれた部分を抽出
    results_to_show: list[str] = extract_enclosed(state.result)
    result_to_show = "".join(results_to_show)

    # OBSで読み取られるファイルに書き込み
    update_user_name(user_name)
    update_comment(comment)
    update_result_to_show(result_to_show)

    # OBSで読み取られるファイルから読み込み（書き込みが成功しているか確認する意味も含む）
    return gr.HTML(value=get_user_name_and_comment_html(get_user_name(), get_comment()))


class AutoWesternAstrologyThreadTask(ThreadTask):
    def __init__(self, name: str, player: AutoAudioPlayer) -> None:
        super().__init__(name)
        self.player = player

    def run(self) -> None:
        """
        Play audio for astrology result in an infinite loop.
        """
        logger.info("Start thread for playing audio")
        while not self.stop_event.is_set():
            try:
                # set the target state to play voice and display info
                self.player.set_target()
                if not self.player.is_playable():
                    time.sleep(1)
                    continue

                # display info in obs
                update_user_info_in_obs(
                    state=self.player.target_state, chat_message=self.player.target_chat
                )
                time.sleep(1)

                # TODO 再生する前にここで何か一言入れていもいいかも

                # play audio
                self.player.play_target()
                time.sleep(1)
            except Exception as e:
                logger.exception(f"Failed to play audio: {e}")
                time.sleep(1)


logging_config.configure_logging()
logger = getLogger(__name__)

# スレッドタスクの初期化
voice_thread_task = VoiceTask("voice", WesternAstrologyStateRepositoryImpl())
result_thread_task = GenerateResultTask(
    "result",
    WesternAstrologyStateRepositoryImpl(),
    YoutubeLiveChatMessageRepositoryImpl(),
)
livechat_thread_task = LivechatTask(
    "livechat",
    WesternAstrologyStateRepositoryImpl(),
    YoutubeLiveChatMessageRepositoryImpl(),
)
waiting_count_display_thread_task = DisplayWaitingCountTreadTask(
    "waiting_count_display",
    WesternAstrologyStateRepositoryImpl(),
    display_format="占い待ち: {}人",
    interval=5,
)
auto_player = AutoAudioPlayer(
    state_repo=WesternAstrologyStateRepositoryImpl(),
    chat_repo=YoutubeLiveChatMessageRepositoryImpl(),
)
auto_system_thread_task = AutoWesternAstrologyThreadTask(
    "auto_system", player=auto_player
)

with gr.Blocks(css=custom_css) as demo:
    gr.HTML(h1_tag("YouTube Live AI占い"))

    gr.HTML(h2_tag("バックグラウンドの処理の管理"))

    gr.HTML(f"""<a href="{GRAFANA_URL}">Progress View </a>""")

    video_id_input = gr.Textbox(
        interactive=True,
        placeholder="YouTube動画IDを入力してください",
        show_label=False,
    )
    with gr.Row():
        btn_livechat_start = gr.Button(
            "コメント取得 START", elem_classes=["custom-start-btn"]
        )
        livechat_status = gr.HTML(div_center_bold_text("未開始"))
        btn_livechat_stop = gr.Button(
            "コメント取得 STOP", elem_classes=["custom-stop-btn"]
        )
    with gr.Row():
        btn_result_start = gr.Button(
            "占い生成 START", elem_classes=["custom-start-btn"]
        )
        result_status = gr.HTML(div_center_bold_text("未開始"))
        btn_result_stop = gr.Button("占い生成 STOP", elem_classes=["custom-stop-btn"])
    with gr.Row():
        btn_voice_start = gr.Button("音声生成 START", elem_classes=["custom-start-btn"])
        voice_status = gr.HTML(div_center_bold_text("未開始"))
        btn_voice_stop = gr.Button("音声生成 STOP", elem_classes=["custom-stop-btn"])
    with gr.Row():
        display_waiting_num_start = gr.Button(
            "待ち人数表示 START", elem_classes=["custom-start-btn"]
        )
        display_waiting_num_status = gr.HTML(div_center_bold_text("未開始"))
        display_waiting_num_stop = gr.Button(
            "待ち人数表示 STOP", elem_classes=["custom-stop-btn"]
        )
    with gr.Row():
        auto_system_start = gr.Button(
            "自動再生 START", elem_classes=["custom-start-btn"]
        )
        auto_system_status = gr.HTML(div_center_bold_text("未開始"))
        auto_system_stop = gr.Button("自動再生 STOP", elem_classes=["custom-stop-btn"])

    btn = gr.Button("データベースを初期化 (全てのデータが消去されます)")
    btn.click(
        fn=initialize_db,
    )

    # 各ボタンのクリック時に対応する関数を呼び出す
    # コメント取得
    btn_livechat_start.click(
        fn=livechat_thread_task.set_live_chat_id, inputs=[video_id_input]
    ).then(fn=livechat_thread_task.start, outputs=livechat_status).then(
        fn=div_center_bold_text,
        inputs=[livechat_status],
        outputs=livechat_status,
    )
    btn_livechat_stop.click(
        fn=livechat_thread_task.stop, inputs=[], outputs=livechat_status
    ).then(
        fn=div_center_bold_text,
        inputs=[livechat_status],
        outputs=livechat_status,
    )
    # 占い結果生成
    btn_result_start.click(
        fn=result_thread_task.start, inputs=[], outputs=result_status
    ).then(
        fn=div_center_bold_text,
        inputs=[result_status],
        outputs=result_status,
    )
    btn_result_stop.click(
        fn=result_thread_task.stop, inputs=[], outputs=result_status
    ).then(
        fn=div_center_bold_text,
        inputs=[result_status],
        outputs=result_status,
    )
    # 音声生成
    btn_voice_start.click(
        fn=voice_thread_task.start, inputs=[], outputs=voice_status
    ).then(
        fn=div_center_bold_text,
        inputs=[voice_status],
        outputs=voice_status,
    )
    btn_voice_stop.click(
        fn=voice_thread_task.stop, inputs=[], outputs=voice_status
    ).then(
        fn=div_center_bold_text,
        inputs=[voice_status],
        outputs=voice_status,
    )
    # 待ち人数表示
    display_waiting_num_start.click(
        fn=waiting_count_display_thread_task.start,
        outputs=display_waiting_num_status,
    ).then(
        fn=div_center_bold_text,
        inputs=[display_waiting_num_status],
        outputs=display_waiting_num_status,
    )
    display_waiting_num_stop.click(
        fn=waiting_count_display_thread_task.stop,
        outputs=display_waiting_num_status,
    ).then(
        fn=div_center_bold_text,
        inputs=[display_waiting_num_status],
        outputs=display_waiting_num_status,
    )
    # 自動再生
    auto_system_start.click(
        fn=auto_system_thread_task.start,
        outputs=auto_system_status,
    ).then(
        fn=div_center_bold_text,
        inputs=[auto_system_status],
        outputs=auto_system_status,
    )
    auto_system_stop.click(
        fn=auto_system_thread_task.stop,
        outputs=auto_system_status,
    ).then(
        fn=div_center_bold_text,
        inputs=[auto_system_status],
        outputs=auto_system_status,
    )

if __name__ == "__main__":
    # 音声の出力先デバイスが利用可能か確認
    from app.application.audio import get_device_info, is_available_device
    from app.config import AUDIO_DEVICE_NAME

    if not is_available_device(AUDIO_DEVICE_NAME):
        info = get_device_info()
        error_msg = (
            f"Configured Device {AUDIO_DEVICE_NAME} is not available.\n"
            f"Please set AUDIO_DEVICE_NAME in config.py from following devices:\n\n{info}"
        )
        raise ValueError(error_msg)

    demo.launch(server_name="0.0.0.0", server_port=7860)  # TODO IPやポートは設定に書く
