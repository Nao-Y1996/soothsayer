# YouTubeライブ配信で占星術をする

## 概要

- YouTubeライブ配信でコメントを取得し、コメントを元に占星術をするという企画で使用するアプリケーション
- 占い結果のを確認、音声ファイルの再生などの操作を行うためのUIを提供する

## 実行環境

- Python: 3.11
- poetry: 1.8系
- Docker:
  - DB: PostgreSQL
  - Grafana


## 環境構築

1. このリポジトリをクローンする

    ```bash
    git clone https://github.com/Nao-Y1996/soothsayer.git
    ```

2. 依存関係をインストールする
    
    poetry2系を使用している場合は `poetry self add poetry-plugin-shell` を実行して、`poetry shell`を利用できるようにしてください
  
    ```bash
    poetry shell
    poetry install --no-root
    ```
3. 必要なファイルの作成

    ```bash
   python setup_init.py
    ```
4. 環境変数のセット

    以下の2つのAPIを利用するためのAPIキーを`.env` にAPIキーを設定してください
    - YouTube Data API v3
    - Generative Language API
    
    以下の環境変数はそのままでも良い

    ```bash
    POSTGRES_USER=user_for_postgres
    POSTGRES_PASSWORD=password_for_postgres
    POSTGRES_DB=db_for_postgres
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    ```

5. データベースを立ち上げる
    
    Dockerを起動して以下のコマンドを実行する 

    ```bash
    docker compose up -d 
    ```

6. テーブルの初期化

    ```bash
    alembic upgrade head
    ```

7. アプリケーションを起動する
  
    初回は少し時間がかかる
  
    ```bash
    python gradio_ui.py
    ```

8. ブラウザで`http://localhost:7860/?__theme=light` にアクセスし、画面が表示されれば環境構築は成功です

## 使用方法

[docs/app_usage.md](docs/app_usage.md)を参照してください

## テーブルの一覧

### youtube_livechat_message

ライブチャットのメッセージを保存するテーブル

| カラム名       | データ型      | 説明                       |
|------------|-----------|--------------------------|
| id         | str       | 主キー                      |
| message    | jsonb     | メッセージの内容やメタデータ全てを含んだjson |
| created_at | timestamp | メッセージの作成日時               |
| updated_at | timestamp | メッセージの更新日時               |

### astrology_status

占星術の状態を保存するテーブル

| カラム名              | データ型  | 説明               |
|-------------------|-------|------------------|
| message_id        | str   | メッセージのID, 主キー    |
| is_target         | bool  | 占い対象かどうか         |
| required_info     | jsonb | 占いをするために必要な情報    |
| result            | text  | 占いの結果            |
| result_voice_path | text  | 音声ファイルのパス        |
| is_played         | bool  | 音声ファイルが再生されたかどうか |

## 処理の詳細

3スレッドの処理とGradioのUIによって構成されている

### スレッド1: ライブ配信のコメント取得

- youtubeAPIを使って占いをするライブ配信に対するコメントを取得し続ける
- 取得したコメントを`youtube_livechat_message`の`message`列に入れる
- `youtube_livechat_message`テーブルから`astrology_result`に`message_id`が存在しないレコードを取得する
- コメントの内容を解析し、占い対象かどうかを判定する（コメントに`占い依頼`キーワードが含まれているかどうか）
- `astrology_result`テーブルに対して、`is_target`を設定した上で保存する

### スレッド2: 占い対象のコメントから占いに必要な情報を取得

- 占い対象のコメント一覧のそれぞれに対して、`message`をLLMに投げて`required_info`を抽出して`astrology_result`テーブルに保存する
- `astrology_result`テーブルから、「`result`がなく、`required_info`がある」レコード一覧を取得する
- レコードのそれぞれに対して`required_info`からLLMのAPIで占い結果を生成する
- 生成され次第、順番に占い結果をテーブルに反映する（`required_info`と`result`を更新する）

### スレッド3: 音声ファイルの生成

- `astrology_state`テーブルから、`result`が存在し、`result_voice_path`がない」レコード一覧を取得する
- レコード一覧のそれぞれに対して、text2speechで音声ファイルを作成してディレクトリに保存する（時間がかかる）
- 保存した音声ファイルのパスをテーブルに反映する（`result_voice_path`を更新する）

### 画面表示

- 更新ボタン: `astrology_state`テーブルから、`required_info`が空ではない（占いに必要な情報抽出が完了した）レコード一覧を取得する
- Progress View のリンク: Grafanaのダッシュボードにリンクしており、データの生成状況が可視化されている
- 3つの START/STOP ボタン: 3つの処理（スレッド）の開始と停止を行う

### その他

#### 占星術の実施方法

- 取り出したコメントが占星術の対象である場合には、`pyswisseph`とLLMを使って占星術を行う

#### 音声ファイルの生成方法

- 占星術の結果(テキスト)を [style-bert-vit2](https://github.com/litagin02/Style-Bert-VITS2)を用いて音声ファイルに変換する
    - この時style-bert-vit2のAPIサーバーを別途立ち上げておく必要がある

## 開発時に使用するコマンド

1. DBに接続する

  ```
  docker build -t my_postgres_image -f Dockerfile_postgres .
  ```

  ```
  docker-compose exec postgres psql -U uranaishi -d uranai
  ```

2. 独自Dockerfileをcomposeを使ってビルドする場合

  ```bash
  docker-compose up --build -d 
  ```

3. マイグレーションを行う

  ```bash
  alembic revision --autogenerate -m "comment"
  alembic upgrade head
  ```

4. DBを含めてコンテナを作り直す

保存したデータやGrafanaのダッシュボードも消えるので注意

  ```bash
  docker-compose down
  docker-compose up --build -d
  ```

## クエリ

便利なクエリを記載しておく。これらはGrafanaで可視化する際にも使用している

### コメントと占い結果の一覧

```sql
SELECT chats.created_at,
       chats.message -> 'snippet' -> 'displayMessage'    as message,
       chats.message -> 'authorDetails' -> 'displayName' as name,
       status.required_info,
       status.result,
       status.result_voice_path
FROM youtube_livechat_messages as chats
         JOIN western_astrology_statuss as status
              on (chats.id = status.message_id)
```

### コメント数

```sql
SELECT COUNT(1) as コメント数
FROM youtube_livechat_messages
```

### 占い依頼数

```sql
SELECT COUNT(1) as 占い依頼数
FROM western_astrology_statuss
WHERE is_target
```

### 準備完了数

```sql
SELECT COUNT(1) as 準備完了数
FROM western_astrology_statuss
WHERE is_target
  and required_info != '{}' --and result is null and result_voice_path is null
```

### 占い完了数

```sql
SELECT COUNT(1) as 占い完了数
FROM western_astrology_statuss
WHERE is_target
  and required_info != '{}' and result != '' and result_voice_path = ''
```

### 音声ファイル生成数

```sql
SELECT COUNT(1) as 音声生成数
FROM western_astrology_statuss
WHERE is_target
  and required_info != '{}' and result != '' and result_voice_path != ''
```

### 音声再生数

```sql
SELECT COUNT(1) as 再生数
FROM western_astrology_statuss
WHERE is_target
  and required_info != '{}' and result != '' and result_voice_path != '' and is_played
```