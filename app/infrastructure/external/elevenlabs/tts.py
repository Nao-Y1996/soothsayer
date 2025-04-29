from logging import getLogger
from pathlib import Path
from typing import Iterator

from elevenlabs.client import ElevenLabs

from app.core.const import ELEVENLABS_API_KEY

logger = getLogger(__name__)

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)


def generate(
    text: str,
    output_file: str | Path,
    voice_id: str = "Mv8AjrYZCBkdsmDHNwcB",
    model_id: str = "eleven_multilingual_v2",
    output_format: str = "mp3_22050_32",
) -> str:
    """
    テキストから音声を生成する。

    Args:
        text (str): 音声に変換するテキスト
        output_file (str | Path): 出力ファイルのパス
        voice_id (str): 音声のID
        model_id (str): モデルのID
        output_format (str): 出力フォーマット

    Returns:
        str: 出力ファイルのパス
    """
    audio = client.generate(
        text=text,
        voice=voice_id,
        model=model_id,
        stream=False,
        output_format=output_format,
    )
    if isinstance(output_file, str):
        output_file = Path(output_file)
    with output_file.open("wb") as f:
        if isinstance(audio, (bytes, bytearray)):
            f.write(audio)
        elif isinstance(audio, Iterator):
            for chunk in audio:
                f.write(chunk)
    return str(output_file)
