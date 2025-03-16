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
prompts_dir = Path(__file__).parent / "prompts"

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
    prompt_path = prompts_dir / "western_astrology.md"
    with prompt_path.open("r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt = prompt_template.format(
        name=name,
        positions_text=positions_text,
        sun_sign=sun_sign,
    )

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
