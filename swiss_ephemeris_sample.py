import logging
from logging import getLogger

import swisseph as swe

logger = getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def calc_swiss_ephemeris_sample() -> None:
    """
    Swiss Ephemerisを使用して天文計算を実行するサンプル
    Swiss Ephemeris は、天文計算用のライブラリで、python経由では pyswisseph ライブラリがある
    アプリでの西洋占星術では pyswisseph 直接使用せずに、flatlib ライブラリを使用している
    flatlib は、pyswisseph をラップして、より使いやすいAPIを提供しているが、
    pyswisseph の古いバージョン（2.08.00-1）を使用しており、更新も止まっているため将来的には pyswisseph を直接使用した方が良い。
    ここでは、pyswisseph を直接使用して、天文計算を実行するサンプルを提供する
    """
    jd = swe.julday(2025, 1, 28, 12.0)
    result = swe.calc_ut(jd, swe.SUN)
    logger.info(f"Julian Date: {jd}")
    logger.info(f"Sun position: {result}")

if __name__ == "__main__":
    calc_swiss_ephemeris_sample()
