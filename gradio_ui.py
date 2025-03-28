# isort: off
from app.core import logging_config  # これにより設定が適用される

# isort: on
from functools import wraps
from logging import getLogger

import gradio as gr

from app.application.audio import play_audio_file
from app.application.generate_audio import VoiceTask
from app.application.generate_result import GenerateResultTask
from app.application.obs_display_service import (
    DisplayWaitingCountTreadTask,
    get_comment,
    get_user_name,
    toggle_visibility_user_info_in_obs,
    update_comment,
    update_result_to_show,
    update_user_name,
)
from app.application.store_livechat import LivechatTask
from app.application.text_service import extract_enclosed
from app.core.const import GRAFANA_URL
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
    AstrologyData,
    LatestGlobalStateView,
    as_code_block,
    custom_css,
    get_chat_html,
    get_info_html,
    get_play_button_name,
    get_user_name_and_comment_html,
)

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

# リポジトリ
western_astrology_repo = WesternAstrologyStateRepositoryImpl()


def initialize_db():
    try:
        init_db()
        gr.Info("データベースを初期化しました.", duration=3)
    except Exception as e:
        raise gr.Error(f"データベースの初期化に失敗しました. {e}", duration=3)


def get_latest_data() -> list[AstrologyData]:
    """
    最新のデータを取得する
    """
    state_list, chat_message_list = (
        western_astrology_repo.get_all_prepared_state_and_message()
    )
    all_astrology_data = []
    for state, message in zip(state_list, chat_message_list, strict=True):
        data: AstrologyData = AstrologyData(chat_message=message, state=state)
        all_astrology_data.append(data)
    return all_astrology_data


def unpack_latest_state_view(func):
    @wraps(func)
    def wrapper(*args, **kwargs) -> tuple[list[AstrologyData], str, str, str, int, str]:
        global_view: LatestGlobalStateView = func(*args, **kwargs)
        return (
            global_view.all_data,
            global_view.info_html,
            global_view.chat_html,
            global_view.astrology_result_text,
            global_view.current_index,
            global_view.play_button_name,
        )

    return wrapper  # type: ignore


@unpack_latest_state_view
def update_data(current_index) -> LatestGlobalStateView:
    """
    表示中の AstrologyData を更新して内容を返す。
    """
    # データを更新する
    data_list: list[AstrologyData] = get_latest_data()

    if not data_list:
        return LatestGlobalStateView(
            all_data=data_list,
            info_html=get_info_html(current_index, data_list),
            chat_html="",
            astrology_result_text=as_code_block(""),
            current_index=current_index,
            play_button_name=get_play_button_name(None),
        )
    if current_index >= len(data_list):
        current_index = 0
    current_data = data_list[current_index]
    return LatestGlobalStateView(
        all_data=data_list,
        info_html=get_info_html(current_index, data_list),
        chat_html=get_chat_html(current_data),
        astrology_result_text=as_code_block(current_data.state.result),
        current_index=current_index,
        play_button_name=get_play_button_name(current_data),
    )


@unpack_latest_state_view
def prev_data(
    current_index: int, data_list: list[AstrologyData]
) -> LatestGlobalStateView:
    """
    「前へ」ボタン：表示中の AstrologyData インデックスをひとつ戻して内容を返す。
    """
    if not data_list:
        current_index = 0
    else:
        current_index = (current_index - 1) % len(data_list)
    current_data = data_list[current_index]
    # return update_data()ともできるが、連打すると更新処理が多すぎてコネクションプールが枯渇する可能性がある
    return LatestGlobalStateView(
        all_data=data_list,
        info_html=get_info_html(current_index, data_list),
        chat_html=get_chat_html(current_data),
        astrology_result_text=as_code_block(current_data.state.result),
        current_index=current_index,
        play_button_name=get_play_button_name(current_data),
    )


@unpack_latest_state_view
def next_data(
    current_index: int, data_list: list[AstrologyData]
) -> LatestGlobalStateView:
    """
    「次へ」ボタン：表示中の AstrologyData インデックスをひとつ進めて内容を返す。
    """
    if not data_list:
        current_index = 0
    else:
        current_index = (current_index + 1) % len(data_list)
    current_data = data_list[current_index]
    # return update_data()ともできるが、連打すると更新処理が多すぎてコネクションプールが枯渇する可能性がある
    return LatestGlobalStateView(
        all_data=data_list,
        info_html=get_info_html(current_index, data_list),
        chat_html=get_chat_html(current_data),
        astrology_result_text=as_code_block(current_data.state.result),
        current_index=current_index,
        play_button_name=get_play_button_name(current_data),
    )


def play_current_audio(
    current_index,
    data_list: list[AstrologyData],
) -> None:
    """
    「再生」ボタン：現在表示中の AstrologyData の voice_path の .wav ファイルを再生する。
    """
    if not data_list:
        return
    data = data_list[current_index]
    # TODO 再生を非同期にする
    play_audio_file(data.state.result_voice_path)
    # 再生済みフラグを更新
    data.state.is_played = True
    western_astrology_repo.save([data.state])


@unpack_latest_state_view
def play_current_audio_ui(current_index, data_list) -> LatestGlobalStateView:
    """
    UI用のラッパー関数。
    再生処理後に update_data を呼び出して最新情報を反映する。
    """
    play_current_audio(current_index, data_list)
    current_data = data_list[current_index]
    # return update_data()ともできるが、連打すると更新処理が多すぎてコネクションプールが枯渇する可能性がある
    return LatestGlobalStateView(
        all_data=data_list,
        info_html=get_info_html(current_index, data_list),
        chat_html=get_chat_html(current_data),
        astrology_result_text=as_code_block(current_data.state.result),
        current_index=current_index,
        play_button_name=get_play_button_name(current_data),
    )


def update_user_info_in_obs(current_index: int, data_list: list[AstrologyData]):
    """
    OBSに表示する情報を更新して返す
    """
    if not data_list:
        return
    current_data = data_list[current_index]
    user_name = current_data.chat_message.authorDetails.displayName
    comment = current_data.chat_message.snippet.displayMessage
    results_to_show: list[str] = extract_enclosed(
        current_data.state.result
    )  # << >> で囲まれた部分を抽出
    result_to_show = "".join(results_to_show)

    # OBSで読み取られるファイルに書き込み
    update_user_name(user_name)
    update_comment(comment)
    update_result_to_show(result_to_show)

    # OBSで読み取られるファイルから読み込み（書き込みが成功しているか確認する意味も含む）
    return gr.HTML(value=get_user_name_and_comment_html(get_user_name(), get_comment()))


with gr.Blocks(css=custom_css) as demo:
    gr.HTML(h1_tag("YouTube Live AI占い"))

    with gr.Row():
        # DBの内容を表示
        with gr.Column(elem_classes=["base-info"]):
            info_html_component = gr.HTML(value=h2_tag("データ"))
            chat_html_component = gr.HTML(value="")
            update_btn = gr.Button("データ更新")
        # OBSに連携される情報を表示
        with gr.Column(elem_classes=["obs-info"]):
            gr.HTML(value=h2_tag("OBS連携"))
            chat_html_component_for_obs = gr.HTML(value="")
            with gr.Row():
                obs_hide_btn = gr.Button("非表示", elem_classes=["obs-hide-btn"])
                obs_update_btn = gr.Button("更新", elem_classes=["obs-update-btn"])
                obs_show_btn = gr.Button("表示", elem_classes=["obs-show-btn"])

    gr.HTML(value=h2_tag("占い結果"))
    astrology_md_component = gr.Markdown(
        value="", elem_classes=["custom-astrology-html"], container=True
    )

    # 内部状態を保持するための hidden state
    state_index = gr.State(0)
    all_data = gr.State([])

    # obsの画面の表示を切り替える
    obs_hide_btn.click(
        fn=toggle_visibility_user_info_in_obs,
        inputs=[gr.State(value=False)],
    )
    obs_show_btn.click(
        fn=toggle_visibility_user_info_in_obs,
        inputs=[gr.State(value=True)],
    )

    obs_update_btn.click(
        fn=update_user_info_in_obs,
        inputs=[state_index, all_data],
        outputs=[chat_html_component_for_obs],
    )

    with gr.Row():
        btn_prev = gr.Button("前へ")
        btn_play = gr.Button(
            get_play_button_name(None), elem_classes=["custom-play-btn"]
        )
        btn_next = gr.Button("次へ")

        # 更新ボタン：DBから最新データを取得して表示を更新
        update_btn.click(
            fn=update_data,
            inputs=[state_index],
            outputs=[
                all_data,
                info_html_component,
                chat_html_component,
                astrology_md_component,
                state_index,
                btn_play,
            ],
        )

    # 前へボタン：内部状態の current_index を更新して表示を切り替え
    btn_prev.click(
        fn=prev_data,
        inputs=[state_index, all_data],
        outputs=[
            all_data,
            info_html_component,
            chat_html_component,
            astrology_md_component,
            state_index,
            btn_play,
        ],
    )

    # 次へボタン：内部状態の current_index を更新して表示を切り替え
    btn_next.click(
        fn=next_data,
        inputs=[state_index, all_data],
        outputs=[
            all_data,
            info_html_component,
            chat_html_component,
            astrology_md_component,
            state_index,
            btn_play,
        ],
    )

    # 再生ボタン：音声再生後、最新状態を反映
    btn_play.click(
        fn=play_current_audio_ui,
        inputs=[state_index, all_data],
        outputs=[
            all_data,
            info_html_component,
            chat_html_component,
            astrology_md_component,
            state_index,
            btn_play,
        ],
    )

    gr.Markdown("-------------------------")
    with gr.Row():
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
