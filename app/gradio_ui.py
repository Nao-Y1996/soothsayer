# isort: off
from app.core import logging_config  # これにより設定が適用される

# isort: on
from functools import wraps
from logging import getLogger

import gradio as gr
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.audio import play_audio_file
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

logging_config.configure_logging()
logger = getLogger(__name__)
engine = create_engine(PG_URL, echo=False)


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
    status_list, chat_message_list = astrology_repo.get_all_prepared_status_and_message()
    all_astrology_data = []
    for status, message in zip(status_list, chat_message_list, strict=True):
        data: AstrologyData = AstrologyData(chat_message=message, status=status)
        all_astrology_data.append(data)
    return all_astrology_data


def get_info_html(current_index: int, data_list: list[AstrologyData]):
    """
    データの情報を表示する HTML を返す。
    リンク先は別のコンテナで立ち上げているGrafanaのダッシュボード
    """
    length = len(data_list)

    return f"""
<h3>データ No. {current_index + 1}/{length}</h3>
"""


def get_chat_html(data: AstrologyData):
    """
    AstrologyData のチャットメッセージを HTML に整形して返す。
    """
    return f"""
<div>
    <span>・from : {data.chat_message.authorDetails.displayName}  ({data.chat_message.snippet.publishedAt})</span></br>
    <span>・コメント : {data.chat_message.snippet.displayMessage}</span></br>
</div>
"""


def get_astrology_html(data: AstrologyData):
    """
    AstrologyData の占星術結果を HTML に整形して返す。
    """
    return f"<div>{data.status.result}</div>"


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
            info_html="データなし",
            chat_html="",
            astrology_html="",
            current_index=current_index,
            play_button_name="",
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
    return update_data(current_index)


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
    return update_data(current_index)


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


def play_current_audio_ui(current_index, data_list) -> LatestGlobalStateView:
    """
    UI用のラッパー関数。
    再生処理後に update_data を呼び出して最新情報を反映する。
    """
    repo = WesternAstrologyResultRepositoryImpl(session=Session(bind=engine))
    play_current_audio(current_index, data_list, repo)
    return update_data(current_index)


def get_play_button_name(data: AstrologyData):
    """ """
    status = data.status
    if status.result_voice_path and not status.is_played:
        btn_name = "再生(未)"
    elif status.result_voice_path and status.is_played:
        btn_name = "再生(済)"
    else:
        btn_name = "音声なし"
    return btn_name


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
.custom-astrology-html {
    border: 1px solid #ccc;  /* 枠線 */
    height: 300px;         /* 固定高さ（例: 300px） */
    overflow-y: scroll;    /* スクロールバーを表示 */
    padding: 10px;         /* 内側の余白 */
}
"""
with gr.Blocks(css=custom_css) as demo:
    gr.HTML(h1_tag("YouTube Live AI占い"))

    update_btn = gr.Button("更新")
    info_html_component = gr.HTML(value="")
    _ = gr.HTML(value=h2_tag("コメント情報"))
    chat_html_component = gr.HTML(value="")
    _ = gr.HTML(value=h2_tag("占い結果"))
    astrology_html_component = gr.Markdown(value="", elem_classes=["custom-astrology-html"])

    # 内部状態を保持するための hidden state
    state_index = gr.State(0)
    all_data = gr.State([])

    with gr.Row():
        btn_prev = gr.Button("前へ")
        btn_play = gr.Button(" ", elem_classes=["custom-play-btn"])
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
