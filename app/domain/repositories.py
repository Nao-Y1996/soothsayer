# ===============================================================
# ドメインオブジェクトが少ないので、各オブジェクトのリポジトリをここに集約する
# ===============================================================

from abc import ABC, abstractmethod

from app.domain.westernastrology import WesternAstrologyStatusEntity
from app.domain.youtube.live import LiveChatMessageEntity


class YoutubeLiveChatMessageRepository(ABC):
    """
    YouTubeライブチャットメッセージの永続化を扱うリポジトリの抽象クラス。
    DDDにおけるRepositoryインターフェースを想定。
    """

    @abstractmethod
    def save(self, messages: list[LiveChatMessageEntity]) -> None:
        """
        メッセージリストをDBに保存または更新する。

        Args:
            messages: 保存したいYoutubeLiveChatMessageエンティティのリスト。
        """
        raise NotImplementedError(
            "save_list method for YoutubeLiveChatMessageRepository must be implemented."
        )

    @abstractmethod
    def get_by_message_ids(self, message_ids: list[str]) -> list[LiveChatMessageEntity]:
        """
        messageカラム内のJSONに含まれる 'id' フィールドが、引数の message_ids のいずれかに
        一致する行を取得し、LiveChatMessageEntity のリストとして返す。

        Args:
            message_ids: 取得したいメッセージのIDリスト。

        Returns:
            IDリストに一致するメッセージのリスト。
        """
        raise NotImplementedError(
            "get_by_message_ids method for YoutubeLiveChatMessageRepository must be implemented."
        )


class WesternAstrologyResultRepository(ABC):
    """
    西洋占星術結果の永続化を扱うリポジトリの抽象クラス。
    DDDにおけるRepositoryインターフェースを想定。
    """

    @abstractmethod
    def save(self, results: list[WesternAstrologyStatusEntity]) -> None:
        """
        占い結果をDBに保存または更新する。
        """
        raise NotImplementedError(
            "save method for WesternAstrologyResultRepository must be implemented."
        )

    @abstractmethod
    def get_not_prepared_target(self, limit: int) -> list[WesternAstrologyStatusEntity]:
        """
        占い対象で、占いに必要な情報がまだないものを取得する
        """
        raise NotImplementedError(
            "get_target method for WesternAstrologyResultRepository must be implemented."
        )

    @abstractmethod
    def get_all_prepared_status_and_message(
        self,
    ) -> tuple[list[WesternAstrologyStatusEntity], list[LiveChatMessageEntity]]:
        """
        占い対象で、占いに必要な情報が揃っているものを全て取得する
        """
        raise NotImplementedError(
            "get_target method for WesternAstrologyResultRepository must be implemented."
        )

    @abstractmethod
    def get_prepared_target_with_no_result(
        self, limit: int
    ) -> list[WesternAstrologyStatusEntity]:
        """
        占い対象で、占いに必要な情報が揃っていて、占い結果がまだないものを取得する
        """
        raise NotImplementedError(
            "get_target method for WesternAstrologyResultRepository must be implemented."
        )

    @abstractmethod
    def get_no_voice_target(self, limit: int) -> list[WesternAstrologyStatusEntity]:
        """
        占い結果があり、音声ファイルがまだないものを取得する
        """
        raise NotImplementedError(
            "get_target method for WesternAstrologyResultRepository must be implemented."
        )

    @abstractmethod
    def get_all_with_voice(self) -> list[WesternAstrologyStatusEntity]:
        """
        音声ファイルがあるものを全て取得する
        """
        raise NotImplementedError(
            "get_all_with_voice method for WesternAstrologyResultRepository must be implemented."
        )
