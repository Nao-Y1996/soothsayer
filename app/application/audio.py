from logging import getLogger

import simpleaudio as sa

from app.config import VOICE_MODEL_NAME
from app.infrastructure.external.stylebertvit2.voice import (
    generate_speech_with_style_bert_vit2,
)

logger = getLogger(__name__)


def play_audio_file(file_path: str) -> None:
    """
    指定された音声ファイル（WAV形式）を再生する関数

    Parameters:
        file_path (str): 再生する音声ファイルのパス
    """
    # WAVファイルを読み込み、再生する
    wave_obj = sa.WaveObject.from_wave_file(file_path)
    play_obj = wave_obj.play()
    play_obj.wait_done()  # 再生が終了するまで待機


def txt_to_audiofile(text: str, audiofile_path: str) -> str:
    """
    テキストを音声に変換し、音声ファイルのパスを返す関数

    Parameters:
        text (str): 変換するテキスト

    Returns:
        str: 音声ファイルのパス

    Raises:
        IOError: 音声ファイルの生成に失敗した場合
    """
    response = generate_speech_with_style_bert_vit2(
        text, VOICE_MODEL_NAME, output_file=audiofile_path
    )
    if response.success:
        return str(response.file_path)
    else:
        raise IOError(response.error_message)
