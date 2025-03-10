from dataclasses import dataclass
from logging import getLogger
from typing import Literal, Optional

import httpx

from app.config import VOICE_HOST, VOICE_PORT

logger = getLogger(__name__)

API_BASE_URI = f"http://{VOICE_HOST}:{VOICE_PORT}"


@dataclass
class TTSResponse:
    success: bool
    file_path: Optional[str] = None
    error_message: Optional[str] = None


def generate_speech_with_style_bert_vit2(
    text: str,
    model_name: Literal[
        "amitaro",
        "koharune-ami",
        "jvnv-F1-jp",
        "jvnv-F2-jp",
        "jvnv-M1-jp",
        "jvnv-M2-jp",
    ],
    model_id: int = 0,
    speaker_id: int = 0,
    sdp_ratio: float = 0.2,
    noise: float = 0.6,
    noisew: float = 0.8,
    length: float = 1.0,
    language: str = "JP",
    auto_split: bool = True,
    split_interval: float = 0.5,
    assist_text: str = "",
    assist_text_weight: float = 1.0,
    style: str = "Neutral",
    style_weight: float = 1.0,
    reference_audio_path: str = "",
    output_file: str = "output.wav",
) -> TTSResponse:
    """
    style_bert_vit2による音声に変換するAPIを呼び出し、音声ファイルを保存する。
    see: https://github.com/litagin02/Style-Bert-VITS2

    Parameters:
        text (str): 変換するテキスト
        model_name (str): 使用する音声モデル名
        model_id (int): モデルID（model_nameが優先される）
        speaker_id (int): 話者ID
        sdp_ratio (float): SDP混合比
        noise (float): サンプルノイズの割合
        noisew (float): SDPノイズの割合
        length (float): 読み上げ速度
        language (str): 言語（JP, EN, ZH）
        auto_split (bool): 改行で分けて生成するか
        split_interval (float): 分割時の無音時間
        assist_text (str): 音声の補助テキスト
        assist_text_weight (float): 補助テキストの強さ
        style (str): スタイル（Neutral など）
        style_weight (float): スタイルの強さ
        reference_audio_path (str): 参照音声パス
        output_file (str): 出力する音声ファイルのパス

    Returns:
        TTSResponse: 成功した場合は `success=True` と `file_path` を返す。
                     失敗した場合は `success=False` と `error_message` を返す。
    """
    params = {
        "text": text,
        "encoding": "utf-8",
        "model_name": model_name,
        "model_id": model_id,
        "speaker_id": speaker_id,
        "sdp_ratio": sdp_ratio,
        "noise": noise,
        "noisew": noisew,
        "length": length,
        "language": language,
        "auto_split": auto_split,
        "split_interval": split_interval,
        "assist_text": assist_text,
        "assist_text_weight": assist_text_weight,
        "style": style,
        "style_weight": style_weight,
        "reference_audio_path": reference_audio_path,
    }

    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(f"{API_BASE_URI}/voice", params=params)

        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            return TTSResponse(success=True, file_path=output_file)

        else:
            return TTSResponse(
                success=False,
                error_message=f"API Error: {response.status_code}, {response.text}",
            )

    except Exception as e:
        return TTSResponse(success=False, error_message=f"Request Error: {str(e)}")


def is_alive():
    """
    ステータスを取得するAPIを呼び出して接続を確認する。

    Returns:
        dict: ステータス情報
    """
    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.get(f"{API_BASE_URI}/status")

        if response.status_code == 200:
            return True

        else:
            logger.error(
                f"style-bert_vit2 might be offline. Error: {response.status_code}, {response.text}"
            )
            return False
    except Exception as e:
        logger.error(f"Failed to get status from style-bert-vit2: {str(e)}")
        return False
