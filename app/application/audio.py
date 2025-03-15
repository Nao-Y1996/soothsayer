from logging import getLogger

import sounddevice as sd
import soundfile as sf

from app.config import AUDIO_DEVICE_NAME, VOICE_MODEL_NAME
from app.infrastructure.external.stylebertvit2.voice import (
    generate_speech_with_style_bert_vit2,
)

logger = getLogger(__name__)


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
