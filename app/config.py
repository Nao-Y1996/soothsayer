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
grafana_url = "http://localhost:3000/goto/gralPCKNR?orgId=1"

# TODO testモードで実行しても実際のyoutubeライブ配信のビデオIDが必要なので、ビデオIDもダミーする
# TODO モードの切り替えを画面から行えるようにする
