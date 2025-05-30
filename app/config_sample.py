from pathlib import Path
from typing import Literal

# testモードではライブチャットので取得したコメントはdummy_messageで置き換えられる
mode_type: Literal["test", "prod"] = "prod"  # test or prod

# 音声ファイルの保存先ディレクトリ（プロジェクトのappディレクトリからの相対パス）
audio_dir = Path("output") / "audio"

# ログファイルの保存先ディレクトリ（プロジェクトのルートディレクトリからの相対パス）
log_dir = Path("log")

# progress viewのURL
grafana_url = "http://localhost:3000/dashboards"

# TODO testモードで実行しても実際のyoutubeライブ配信のビデオIDが必要なので、ビデオIDもダミーする
# TODO モードの切り替えを画面から行えるようにする

# ===== TTSモデル設定 ======
USE_LOCAL = True  # True: style-bert-vit2, False: elevenlabs
# =========================

# ===== style-bert-vit2 の連携 ======
VOICE_HOST = "localhost"
VOICE_PORT = 5050
VOICE_MODEL_NAME = "amitaro"
# ===================================

# ======= elevenlabsの設定 =======
ELEVENLABS_VOICE_ID = "Mv8AjrYZCBkdsmDHNwcB"
ELEVENLABS_MODEL = "eleven_multilingual_v2"
# ===============================

# ======= 音声出力先の設定 ========
AUDIO_DEVICE_NAME = ""  # ex: VB-Cable
# ================================

# ============= OBS連携 =============
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "some_password"

# 画面設定
OBS_SCENE_NAME = "サンプルシーン"
OBS_SOURCE_NAME_FOR_GROUP = "uranai"
USER_NAME_FILE_PATH = (
    Path(__file__).resolve().parent / "interfaces" / "obs" / "texts" / "username.txt"
)
COMMENT_FILE_PATH = (
    Path(__file__).resolve().parent / "interfaces" / "obs" / "texts" / "comment.txt"
)
WAITING_DISPLAY_FILE_PATH = (
    Path(__file__).resolve().parent
    / "interfaces"
    / "obs"
    / "texts"
    / "waiting_display.txt"
)
RESULT_FILE_PATH = (
    Path(__file__).resolve().parent / "interfaces" / "obs" / "texts" / "result.txt"
)
# ===================================

if __name__ == "__main__":
    print(log_dir)
    print(grafana_url)
    print(OBS_HOST)
    print(OBS_PORT)
    print(OBS_PASSWORD)
    print(OBS_SCENE_NAME)
    print(OBS_SOURCE_NAME_FOR_GROUP)
    print(USER_NAME_FILE_PATH)
    print(COMMENT_FILE_PATH)
