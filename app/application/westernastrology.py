import urllib.parse
from logging import getLogger
from pathlib import Path

import httpx
import swisseph as swe
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

from app.core.const import CITY_LOCATION_MAP, PREFECTURE_LOCATION_MAP
from app.domain.westernastrology import InfoForAstrologyEntity, LocationEntity
from app.infrastructure.external.llm.dtos import StructuredOutput
from app.infrastructure.external.llm.llm_google import get_structured_output
from app.infrastructure.external.llm.utils import pydantic_to_markdown

logger = getLogger(__name__)

setup_dir = Path(__file__).parent / "ephemeris"


def get_coordinates(place: str) -> LocationEntity:
    """
    Get static coordinates for a place.
    """
    # 都道府県名から緯度経度を取得
    latitude_longitude = PREFECTURE_LOCATION_MAP.get(place, None)
    # 緯度経度を取得できない場合は、市町村名から緯度経度を取得
    if not latitude_longitude:
        latitude_longitude = CITY_LOCATION_MAP.get(place, None)
    # 緯度経度を取得できない場合は、東京の緯度経度を返す
    if not latitude_longitude:
        latitude_longitude = PREFECTURE_LOCATION_MAP["東京"]
    latitude, longitude = latitude_longitude
    return LocationEntity(latitude=latitude, longitude=longitude)


def extract_info_for_astrology(name: str, _input: str) -> InfoForAstrologyEntity:
    """
    Extract human information from input text for astrology.
    """

    result: StructuredOutput = get_structured_output(
        cls=InfoForAstrologyEntity,
        prompt=f"""
extract birthday, birth_time, birthplace from give info.
format is below.

## format
{pydantic_to_markdown(InfoForAstrologyEntity)}

## info
{_input}
""",
    )
    result.model.name = name
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
    location = get_coordinates(place=birthplace)
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


if __name__ == "__main__":
    from app.infrastructure.external.llm.llm_google import get_output as gemini

    human_info = extract_info_for_astrology(
        name="太郎",
        _input="2000年の12月3日の午後7時に東京で生まれです",
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
