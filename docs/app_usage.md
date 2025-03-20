
## 準備


1. Dokcerを立ち上げる
2. style-bert-vit2のAPIサーバーを立ち上げる

    占いの音声化には [Style-Bert-VITS2](https://github.com/litagin02/Style-Bert-VITS2)を利用しているため、APIサーバーを立ち上げてください。
    リポジトリのディレクトリで、以下のコマンドを実行します。なお、入力文字数などの設定は[ドキュメント](https://github.com/litagin02/Style-Bert-VITS2?tab=readme-ov-file#api-server)に従って変更してください
    
    ```
    python server_fastapi.py
    ```
   
### 起動

1. DBとGrafanaを立ち上げる

  ```bash
  docker-compose up -d
  ```

2. アプリケーションを起動する

  ```bash
  poetry run python gradio_ui.py
  ```

3. ブラウザで`http://localhost:7860/?__theme=light` にアクセスする

### 終了

1. アプリを起動したターミナルで `Ctrl + C` を押して終了する

2. DBとGrafanaを終了する

  ```bash
  docker-compose down
  ```

## 設定

### テスト用コメントでの動作

- `app/config.py` の以下の部分で "test" か "prod" を指定可能。
- testの場合、テスト用のコメントを使用して動作する
- prodの場合、YouTubeのコメントを使用して動作する

```python
mode_type: Literal["test", "prod"] = "test"  # test or prod
```

### 占いプロンプトの変更

- `app/application/prompts/western_astrology.md` を編集することで、占いのプロンプトを変更できます。
- 変数名（{}で囲まれた部分）は変更せずに利用してください
  - 例: {positions_text}, {name}

### OBSの設定
#### テキストソースの設定
- ユーザー名を表示するテキストソースを作成
  - Text input mode を `From file` に設定し、ファイルパスを `app/interfaces/obs/texts/username.txt` に設定してください
- コメントを表示するテキストソースを作成
  - Text input mode を `From file` に設定し、ファイルパスを `app/interfaces/obs/texts/comment.txt` に設定してください
- 占いの待ち人数を表示するテキストソースを作成
  - Text input mode を `From file` に設定し、ファイルパスを `app/interfaces/obs/texts/waiting_display.txt` に設定してください
- 占い結果の一部分を表示するテキストソースを作成
  - Text input mode を `From file` に設定し、ファイルパスを `app/interfaces/obs/texts/result.txt` に設定してください
- 上記4つの**テキストソースをまとめるためのグループ**を作成

#### webソケットの設定
- OBSのWEBソケットサーバー設定 （`tools` → `WebSocket Server Setting`）
  - `Enable WebSocket server` にチェックを入れてください
  - OBS_PORT: OBSのWEBソケットサーバー設定の、サーバーポート番号
  - OBS_PASSWORD: OBSのWEBソケットサーバー設定の、パスワード（認証を使用している場合のみ）

#### configでの設定
- `app/config.py` の以下の部分で OBS に合わせて設定を変更してください
  - OBS_SCENE_NAME: OBSのシーン名
  - OBS_SOURCE_NAME_FOR_GROUP: テキストソースをまとめるためのグループ名