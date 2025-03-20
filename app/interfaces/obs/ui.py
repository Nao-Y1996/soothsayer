import datetime

from pydantic import BaseModel

from app.domain.westernastrology import WesternAstrologyStateEntity
from app.domain.youtube.live import LiveChatMessageEntity
from app.interfaces.gradio_app.constract_html import h2_tag


class AstrologyData(BaseModel):
    chat_message: LiveChatMessageEntity
    state: WesternAstrologyStateEntity


class LatestGlobalStateView(BaseModel):
    """
    最新の画面表示用データを保持するオブジェクト
    """

    all_data: list[AstrologyData]
    info_html: str
    chat_html: str
    astrology_result_text: str
    current_index: int
    play_button_name: str


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


def get_play_button_name(data: AstrologyData | None):
    """ """
    if not data:
        return "音声なし"
    state = data.state
    if state.result_voice_path and not state.is_played:
        btn_name = "再生(未)"
    elif state.result_voice_path and state.is_played:
        btn_name = "再生(済)"
    else:
        btn_name = "音声なし"
    return btn_name


def as_code_block(text: str) -> str:
    return "```\n" + text + "\n```"


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
