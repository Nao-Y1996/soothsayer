# isort: off
from app.core import logging_config  # これにより設定が適用される

# isort: on
import datetime
from functools import wraps
from logging import getLogger

import gradio as gr
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.audio import play_audio_file
from app.config import (
    OBS_SCENE_NAME,
    OBS_SOURCE_NAME_FOR_GROUP_OF_USER_NANE_AND_COMMENT,
)
from app.core.const import GRAFANA_URL, PG_URL
from app.domain.repositories import WesternAstrologyResultRepository
from app.domain.westernastrology import WesternAstrologyStatusEntity
from app.domain.youtube.live import LiveChatMessageEntity
from app.infrastructure.repositoriesImpl import WesternAstrologyResultRepositoryImpl
from app.interfaces.gradio_app.constract_html import (
    div_center_bold_text,
    h1_tag,
    h2_tag,
)
from app.interfaces.gradio_app.thread_manager import (
    start_livechat,
    start_result,
    start_voice_generate,
    stop_livechat,
    stop_result,
    stop_voice_generate,
)
from app.interfaces.obs.utils import (
    get_comment,
    get_scene_item_id_by_name,
    get_user_name,
    set_scene_item_enabled,
    update_comment,
    update_user_name,
)

logging_config.configure_logging()
logger = getLogger(__name__)
engine = create_engine(PG_URL, echo=False, pool_size=10, max_overflow=5)


class AstrologyData(BaseModel):
    chat_message: LiveChatMessageEntity
    status: WesternAstrologyStatusEntity


class LatestGlobalStateView(BaseModel):
    """
    最新の画面表示用データを保持するオブジェクト
    """

    all_data: list[AstrologyData]
    info_html: str
    chat_html: str
    astrology_html: str
    current_index: int
    play_button_name: str


def get_latest_data() -> list[AstrologyData]:
    """
    最新のデータを取得する
    """
    astrology_repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    status_list, chat_message_list = (
        astrology_repo.get_all_prepared_status_and_message()
    )
    all_astrology_data = []
    for status, message in zip(status_list, chat_message_list, strict=True):
        data: AstrologyData = AstrologyData(chat_message=message, status=status)
        all_astrology_data.append(data)
    return all_astrology_data


def get_jp_time(_datatime: datetime) -> str:
    time_dt_ja = datetime.timedelta(hours=9)
    return (_datatime + time_dt_ja).strftime("%H:%M:%S")


def get_info_html(current_index: int, data_list: list[AstrologyData]):
    """
    データの情報を表示する HTML を返す。
    """
    current_data = data_list[current_index] if data_list else None
    if not current_data:
        return h2_tag("データ")

    length = len(data_list)
    return h2_tag(
        f"データ No. {current_index + 1}/{length}（{get_jp_time(current_data.chat_message.snippet.publishedAt)}）"
    )


def get_chat_html(data: AstrologyData):
    """
    AstrologyData のチャットメッセージを HTML に整形して返す。
    """

    return get_user_name_and_comment_html(
        data.chat_message.authorDetails.displayName,
        data.chat_message.snippet.displayMessage,
    )


def get_user_name_and_comment_html(user_name: str, comment: str):

    return f"""
<div style="padding: 0; margin: 0;">
    <span style="font-size: 1rem; font-weight: bold;">{user_name}</span>
    <textarea readonly style="width: 100%; height: 70px; border-color: #ccc;">{comment}</textarea>
</div>
"""


def get_astrology_html(data: AstrologyData):
    """
    AstrologyData の占星術結果を HTML に整形して返す。
    """
    return f"{data.status.result}"


def unpack_latest_state_view(func):
    @wraps(func)
    def wrapper(*args, **kwargs) -> tuple[list[AstrologyData], str, str, str, int, str]:
        global_view: LatestGlobalStateView = func(*args, **kwargs)
        return (
            global_view.all_data,
            global_view.info_html,
            global_view.chat_html,
            global_view.astrology_html,
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
            astrology_html="",
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
        astrology_html=get_astrology_html(current_data),
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
        astrology_html=get_astrology_html(current_data),
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
        astrology_html=get_astrology_html(current_data),
        current_index=current_index,
        play_button_name=get_play_button_name(current_data),
    )


def play_current_audio(
    current_index,
    data_list: list[AstrologyData],
    astro_repo: WesternAstrologyResultRepository,
) -> None:
    """
    「再生」ボタン：現在表示中の AstrologyData の voice_path の .wav ファイルを再生する。
    """
    if not data_list:
        return
    data = data_list[current_index]
    # TODO 再生を非同期にする
    play_audio_file(data.status.result_voice_path)
    # 再生済みフラグを更新
    data.status.is_played = True
    astro_repo.save([data.status])

@unpack_latest_state_view
def play_current_audio_ui(current_index, data_list) -> LatestGlobalStateView:
    """
    UI用のラッパー関数。
    再生処理後に update_data を呼び出して最新情報を反映する。
    """
    repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    play_current_audio(current_index, data_list, repo)
    current_data = data_list[current_index]
    # return update_data()ともできるが、連打すると更新処理が多すぎてコネクションプールが枯渇する可能性がある
    return LatestGlobalStateView(
        all_data=data_list,
        info_html=get_info_html(current_index, data_list),
        chat_html=get_chat_html(current_data),
        astrology_html=get_astrology_html(current_data),
        current_index=current_index,
        play_button_name=get_play_button_name(current_data),
    )


def get_play_button_name(data: AstrologyData | None):
    """ """
    if not data:
        return "音声なし"
    status = data.status
    if status.result_voice_path and not status.is_played:
        btn_name = "再生(未)"
    elif status.result_voice_path and status.is_played:
        btn_name = "再生(済)"
    else:
        btn_name = "音声なし"
    return btn_name


def update_user_info_in_obs(current_index: int, data_list: list[AstrologyData]):
    """
    OBSに表示する情報を更新して返す
    """
    if not data_list:
        return
    current_data = data_list[current_index]
    user_name = current_data.chat_message.authorDetails.displayName
    comment = current_data.chat_message.snippet.displayMessage

    # OBSで読み取られるファイルに書き込み
    update_user_name(user_name)
    update_comment(comment)

    # OBSで読み取られるファイルから読み込み（書き込みが成功しているか確認する意味も含む）
    return gr.HTML(value=get_user_name_and_comment_html(get_user_name(), get_comment()))


def enable_user_info_in_obs(enable: bool):
    source_id_for_user_name = get_scene_item_id_by_name(
        OBS_SCENE_NAME, OBS_SOURCE_NAME_FOR_GROUP_OF_USER_NANE_AND_COMMENT
    )
    set_scene_item_enabled(
        scene_name=OBS_SCENE_NAME, scene_item_id=source_id_for_user_name, enabled=enable
    )


def hide_user_info():
    enable_user_info_in_obs(False)


def show_user_ingo():
    enable_user_info_in_obs(True)


custom_css = """
/* バックグランド処理のボタン */
.custom-start-btn {
    background-color: #2196F3 !important;
    color: #FFFFFF !important;
    round: 5px;
}
.custom-stop-btn {
    background-color: #F44336 !important;
    color: #FFFFFF !important;
}
.custom-play-btn {
    background-color: #4CAF50 !important;
    color: #FFFFFF !important;
}

/* OBS連携に関係するもの */
.obs-info {
    border: 1px solid #1c2b70;
    border-radius: 6px;
    padding: 7px;
}
.obs-hide-btn {
    background-color: #e6e6e8;
    color: #1c2b70;
}
.obs-update-btn {
    background-color: #1c2b70;
    color: #FFFFFF !important;
}
.obs-show-btn {
    background-color: #e6e6e8;
    color: #1c2b70;
}

/* 占い結果のテキスト */
.base-info {
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 7px;
}
.custom-astrology-html {
    border: 1px solid #ccc;  /* 枠線 */
    height: 300px;         /* 固定高さ（例: 300px） */
    overflow-y: scroll;    /* スクロールバーを表示 */
}
span.svelte-7ddecg p {  /* 要素は実際にHTMLを確認して適切なセレクタを指定 */
    margin-left: 10px;
    margin-right: 10px;
}
"""
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
    astrology_html_component = gr.Markdown(
        value="", elem_classes=["custom-astrology-html"]
    )

    # 内部状態を保持するための hidden state
    state_index = gr.State(0)
    all_data = gr.State([])

    # obsの画面の表示を切り替える
    obs_hide_btn.click(
        fn=hide_user_info,
    )
    obs_show_btn.click(
        fn=show_user_ingo,
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
                astrology_html_component,
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
            astrology_html_component,
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
            astrology_html_component,
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
            astrology_html_component,
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

    # 各ボタンのクリック時に対応する関数を呼び出す
    btn_livechat_start.click(
        fn=start_livechat, inputs=[video_id_input], outputs=livechat_status
    )
    btn_livechat_stop.click(fn=stop_livechat, inputs=[], outputs=livechat_status)

    btn_result_start.click(fn=start_result, inputs=[], outputs=result_status)
    btn_result_stop.click(fn=stop_result, inputs=[], outputs=result_status)

    btn_voice_start.click(fn=start_voice_generate, inputs=[], outputs=voice_status)
    btn_voice_stop.click(fn=stop_voice_generate, inputs=[], outputs=voice_status)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)  # TODO IPやポートは設定に書く
