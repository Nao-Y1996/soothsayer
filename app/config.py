from pathlib import Path
from typing import Literal

# testモードではライブチャットので取得したコメントはdummy_messageで置き換えられる
mode_type: Literal["test", "prod"] = "test"  # test or prod

# テスト用のダミーデータ
dummy_message = "【占い依頼】1990/2/3 午後7時 東京生まれです。 "
dummy_user_name = "太郎"

# 動画ファイルの保存先ディレクトリ（プロジェクトのappディレクトリからの相対パス）
video_dir = Path("output") / "video"

# ログファイルの保存先ディレクトリ（プロジェクトのルートディレクトリからの相対パス）
log_dir = Path("log")

# progress viewのURL
grafana_url = "http://localhost:3000/dashboards"

# TODO testモードで実行しても実際のyoutubeライブ配信のビデオIDが必要なので、ビデオIDもダミーする
# TODO モードの切り替えを画面から行えるようにする


# ============= OBS連携 =============
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "some_password"

# 画面設定
OBS_SCENE_NAME = "サンプルシーン"
OBS_SOURCE_NAME_FOR_GROUP_OF_USER_NANE_AND_COMMENT = "uranai"
USER_NAME_FILE_PATH = (
    Path(__file__).resolve().parent / "interfaces" / "obs" / "texts" / "username.txt"
)
COMMENT_FILE_PATH = (
    Path(__file__).resolve().parent / "interfaces" / "obs" / "texts" / "comment.txt"
)
# ===================================

if __name__ == "__main__":
    print(dummy_message)
    print(dummy_user_name)
    print(video_dir)
    print(log_dir)
    print(grafana_url)
    print(OBS_HOST)
    print(OBS_PORT)
    print(OBS_PASSWORD)
    print(OBS_SCENE_NAME)
    print(OBS_SOURCE_NAME_FOR_GROUP_OF_USER_NANE_AND_COMMENT)
    print(USER_NAME_FILE_PATH)
    print(COMMENT_FILE_PATH)
