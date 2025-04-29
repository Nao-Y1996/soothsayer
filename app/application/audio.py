from logging import getLogger

import sounddevice as sd
import soundfile as sf
from elevenlabs.client import ElevenLabs

from app.config import (
    AUDIO_DEVICE_NAME,
    ELEVENLABS_MODEL,
    ELEVENLABS_VOICE_ID,
    VOICE_MODEL_NAME,
)
from app.core.const import ELEVENLABS_API_KEY
from app.infrastructure.external.elevenlabs.tts import generate
from app.infrastructure.external.stylebertvit2.voice import (
    generate_speech_with_style_bert_vit2,
)

logger = getLogger(__name__)

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)


def play_audio_file(file_path: str) -> None:

    if not is_available_device(AUDIO_DEVICE_NAME):
        info = get_device_info()
        error_msg = f"Device {AUDIO_DEVICE_NAME} is not available. Following devices are available:\n{info}\n Please check the config.py"
        raise ValueError(error_msg)

    play_audio_to_device(file_path, AUDIO_DEVICE_NAME)


def play_audio_to_device(file_path, device_name: str) -> None:
    """
    play audio file to specific device

    Parameters:
        file_path (str): path to audio file
        device_name (str): device name
    """
    data, samplerate = sf.read(file_path)
    sd.play(data, samplerate, device=device_name)
    sd.wait()


def is_available_device(device_name: str):
    """
    check device index from device name

    Parameters:
        device_name (str): device name

    Returns:
        int: device index
    """
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if device["name"] == device_name:
            return True
    return False


def get_device_info():
    devices = sd.query_devices()
    info = ""
    for idx, device in enumerate(devices):
        name = device["name"]
        in_channels = device["max_input_channels"]
        out_channels = device["max_output_channels"]
        info += f"Index: {idx} | Name: {name} | Input Channels: {in_channels} | Output Channels: {out_channels}\n"
    return info


def txt_to_audiofile(text: str, audiofile_path: str, use_local=False) -> str:
    """
    テキストを音声に変換し、音声ファイルのパスを返す関数

    Parameters:
        text (str): 変換するテキスト
        audiofile_path (str): 出力する音声ファイルのパス
        use_local (bool): Trueの場合はローカルの音声モデルを使用する

    Returns:
        str: 音声ファイルのパス

    Raises:
        IOError: 音声ファイルの生成に失敗した場合
    """
    if use_local:
        response = generate_speech_with_style_bert_vit2(
            text, VOICE_MODEL_NAME, output_file=audiofile_path
        )
        if response.success:
            return str(response.file_path)
        else:
            raise IOError(response.error_message)
    else:
        try:
            return generate(
                text=text,
                output_file=audiofile_path,
                voice_id=ELEVENLABS_VOICE_ID,
                model_id=ELEVENLABS_MODEL,
            )
        except Exception as e:
            raise IOError(f"Error generating audio by ElevenLabs: {e}")
