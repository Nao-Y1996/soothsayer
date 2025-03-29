from logging import getLogger

from app.application.audio import play_audio_file
from app.domain.repositories import (
    WesternAstrologyStateRepository,
    YoutubeLiveChatMessageRepository,
)
from app.domain.westernastrology import WesternAstrologyStateEntity
from app.domain.youtube.live import LiveChatMessageEntity

logger = getLogger(__name__)


class AutoAudioPlayer:
    def __init__(
        self,
        state_repo: WesternAstrologyStateRepository,
        chat_repo: YoutubeLiveChatMessageRepository,
    ) -> None:
        self.state_repo = state_repo
        self.chat_repo = chat_repo
        self.target_state: WesternAstrologyStateEntity | None = None
        self.target_chat: LiveChatMessageEntity | None = None

    def _reset_target(self) -> None:
        self.target_state = None
        self.target_chat = None

    def is_playable(self) -> bool:
        if self.target_state is None or self.target_chat is None:
            return False
        return True

    def set_target(self) -> None:
        """
        Set the target state to play audio.
        """
        state_list = self.state_repo.get_should_play_audio_status()
        if not state_list:
            self._reset_target()
            return
        self.target_state = state_list[0]

        chat_messages: list = self.chat_repo.get_by_message_ids(
            [self.target_state.message_id]
        )
        if not chat_messages:
            # TODO: state.message_id は chat_messageのidを外部キーとして持っているので、ここでエラーになることはないはず
            #  DBでJoinして取得するように修正する
            raise RuntimeError(
                f"Failed to get chat message for message_id={self.target_state.message_id}"
            )
        self.target_chat = chat_messages[0]

    def play_target(self) -> None:
        """
        Play the oldest voice audio of the astrology result.
        """
        if not self.is_playable():
            return
        logger.info(
            f"Start playing audio for astrology result: (message_id={self.target_state.message_id})"
        )
        play_audio_file(self.target_state.result_voice_path)
        self.target_state.is_played = True
        self.state_repo.save([self.target_state])
        logger.info(
            f"Succeeded to play audio for astrology result: (message_id={self.target_state.message_id})"
        )
