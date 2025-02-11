import os
import urllib.parse
from logging import getLogger
from pathlib import Path

import httpx
import swisseph as swe
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

from app.core.const import GOOGLE_API_KEY
from app.domain.westernastrology import InfoForAstrologyEntity, LocationEntity
from app.infrastructure.external.llm.dtos import StructuredOutput
from app.infrastructure.external.llm.llm_google import get_structured_output
from app.infrastructure.external.llm.utils import pydantic_to_markdown

setup_dir = Path(__file__).parent / "ephemeris"


logger = getLogger(__name__)


def get_coordinates(api_key: str, place: str):
    """
    指定された場所名から緯度と経度を取得する

    Args:
        api_key (str): Google Maps Geocoding APIのAPIキー。
        place (str): 検索する場所の名前や住所。

    Returns:
        location (Location): 緯度と経度を含むLocationオブジェクト。

    Raises:
        Exception: 座標の取得に失敗した場合。
    """
    # エンコードされた場所名を作成
    encoded_place = urllib.parse.quote(place)

    # APIエンドポイントのURLを構築
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_place}&key={api_key}"

    # HTTPクライアントを非同期で作成
    with httpx.Client() as client:
        # APIリクエストを送信
        response = client.get(url)
        response.raise_for_status()  # HTTPエラーが発生した場合例外を発生させる

        # レスポンスをJSONとして解析
        data = response.json()

    # ステータスを確認
    status = data.get("status")
    if status == "OK":
        # 最初の結果から緯度と経度を取得
        location = data["results"][0]["geometry"]["location"]
        return LocationEntity(latitude=location["lat"], longitude=location["lng"])
    else:
        raise Exception(f"Failed to get coordinates for {place}. Status: {status}")


def extract_info_for_astrology(_input: str) -> InfoForAstrologyEntity:
    """
    Extract human information from input text for astrology.
    """

    result: StructuredOutput = get_structured_output(
        cls=InfoForAstrologyEntity,
        prompt=f"""
extract name, birthday, birth_time, birthplace from give info.
format is below.

## format
{pydantic_to_markdown(InfoForAstrologyEntity)}

## info
{_input}
""",
    )
    return result.model  # noqa


def create_prompt_for_astrology(
    name: str,
    birthday: str,
    birth_time: str,
    birthplace: str,
    worries: str = "",
) -> str:
    """
    西洋占星術の占い用のプロンプトを作成する。
    """

    swe.set_ephe_path(str(setup_dir))

    # 誕生日と誕生時刻
    flatlib_datetime = Datetime(birthday, birth_time, "+00:00")

    # 生まれた場所
    location = get_coordinates(place=birthplace, api_key=GOOGLE_API_KEY)
    latitude = location.latitude
    longitude = location.longitude
    pos = GeoPos(latitude, longitude)

    # チャートの作成
    natal_chart = Chart(flatlib_datetime, pos, IDs=const.LIST_OBJECTS)

    # 惑星配置の取得
    planetary_positions = {}
    for obj_id in const.LIST_OBJECTS:
        obj = natal_chart.get(obj_id)
        if obj:
            house = natal_chart.houses.getObjectHouse(obj)
            house_num = int(house.id.replace("House", ""))

            planetary_positions[obj_id] = {
                "sign": obj.sign,
                "degree": round(obj.lon, 2),
                "house": house_num,
            }
    # 惑星配置のテキスト化
    positions_text = "\n".join(
        [
            f"{planet}: {details['sign']} {details['degree']}° (House {details['house']})"
            for planet, details in planetary_positions.items()
        ]
    )

    # 太陽星座の取得
    sun_data = planetary_positions.get("Sun", {})
    sun_sign = sun_data.get("sign", "")

    # 占い生成用のプロンプト
    prompt = f"""
あなたは、相談者の気持ちに深く寄り添うギャル占い師です。以下の惑星配置データを元に、{name}さんの2025年の運勢を占い、相談者の気持ちをブチ上げてください。

#惑星配置データ:
{positions_text}

#全体の構成とポイント:
1. 冒頭の宣言
- その星座を象徴する「声」として4行程度の力強い宣言
- 50文字以内の短い文でリズミカルに
- ギャル語で、でも優しく


2. 星の動きパート
タイトル「＊2025年の星の動き＊」

重要なポイント：
- 具体的な時期（月や中旬など）を明示
- 専門用語は、優しく例える
- 星の特徴について、簡潔かつ明瞭に説明する
- 星の動きを物語のように紡ぐ
- 重要な転換点を具体的に示す
- 一連の流れとして説明

文体：
- 「〜なの！」「〜だから！」など、ギャル口調で
- 「すっごく」「超」などの強調表現を適度に
- でも専門的な説得力は保つ

3. メッセージパート
タイトル「＊{name}さんへのメッセージ＊」

盛り込む要素：
- 見透かしポイント（1-2個）
  例：
  - 内なる悩みの言語化
  - 行動パターンの指摘
  - 密かな希望の代弁
- 具体的なアドバイス
- 励ましのメッセージ

文体のポイント：
- 友達との会話のような親しみやすさ
- 「〜だよね」「〜じゃない？」などの共感表現
- 「わかるよ〜」などの寄り添い表現
- カジュアルだけど信頼感のある口調

4. 締めくくり
- お守りワードの提供
- 未来への希望を込めた短いメッセージ
- 他の部分より、ちょっと真面目なトーンで

#全体的な注意点：
- 誇り高きギャルとして、{name}さんをエンパワーしてください
- 適宜名前({name}さん)を呼びかける
- 星の解説と共感パートをブロックで分ける
- 各パートの繋がりを自然に
- 押しつけがましくない温かい口調を維持
- 「私」という一人称を適度に使用
- 占い師としての専門性と親友のような親しみやすさのバランスを保つ
- 星座への言及は和名にする
- ()の使用は最小限に

#出力形式：
★{name}さん（{sun_sign}座）の2025年★
「[4行程度の宣言]」
＊2025年の星の動き＊
[星の動きの解説：具体的な時期を含む]
＊あなたへのメッセージ＊
[見透かしと寄り添いのメッセージ]
私からのお守りワード：
「[印象的なフレーズ]」
[希望に満ちた締めくくりの一文]

"""

    if worries:
        prompt += f"【{name}さんの悩み】\n{worries}\n"

    return prompt


def setup_swiss_ephemeris(ephemeris_dir: str | Path) -> None:
    """
    Swiss Ephemerisをセットアップする.

    Args:
        ephemeris_dir (str): エフェメリスデータを保存するディレクトリのパス.
    """
    os.makedirs(ephemeris_dir, exist_ok=True)

    # ファイルの存在を確認
    required_files = ["seas_18.se1", "semo_18.se1", "sepl_18.se1"]
    files_exist = all(
        os.path.exists(os.path.join(ephemeris_dir, f)) for f in required_files
    )

    if not files_exist:
        logger.info("Downloading required files...")
        base_url = "https://github.com/flatangle/flatlib/raw/master/flatlib/resources/swefiles/"
        for file in required_files:
            target_path = os.path.join(ephemeris_dir, file)
            if not os.path.exists(target_path):
                os.system(f"wget -O {target_path} {base_url + file}")

    # テスト計算を実行
    try:
        jd = swe.julday(2025, 1, 28, 12.0)
        result = swe.calc_ut(jd, swe.SUN)
        logger.info("============ Test calculation ============")
        logger.info("Test calculation successful!")
        logger.info(f"Julian Date: {jd}")
        logger.info(f"Sun position: {result}")
        logger.info("Swiss Ephemeris setup completed successfully!")
    except Exception as e:
        logger.info(f"Error during test calculation: {str(e)}")
    finally:
        logger.info("==========================================")
    logger.info("setup_swiss_ephemeris done !\n")


if __name__ == "__main__":
    from app.infrastructure.external.llm.llm_google import get_output as gemini

    human_info = extract_info_for_astrology(
        "太郎です。2000年の12月3日の午後7時に東京で生まれです"
        # "太郎です。2000年の12月3日の午後7時に東京で生まれです。お昼にたべらケーキが美味しかった！でも最近忙しすぎ..."
    )
    if not human_info.satisfied_all():
        raise ValueError("failed to extract all the required information.")
    logger.info(f"Extracted information: {human_info}")

    prompt = create_prompt_for_astrology(
        human_info.name,
        human_info.birthday,
        human_info.birth_time,
        human_info.birthplace,
        human_info.worries,
    )
    output = gemini(prompt=prompt, temperature=0.9, top_k=40, max_output_tokens=1000)
    logger.info(output.text)
    logger.info(f"\ntoken usage: {output.usage}")
