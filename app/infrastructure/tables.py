from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db_common import Base, TableNameMixin, TimestampMixin


class YoutubeLivechatMessageOrm(Base, TimestampMixin, TableNameMixin):
    # 主キー: UUID (insert時に決める)
    id: Mapped[str] = mapped_column(
        primary_key=True,
    )
    # postgres jsonb column
    message: Mapped[dict] = mapped_column(JSONB, nullable=False)


class WesternAstrologyStatusOrm(Base, TimestampMixin, TableNameMixin):
    # 主キー: UUID (insert時に決める)
    # id: Mapped[str] = mapped_column(
    #     primary_key=True,
    # )
    # 主キーかつ外部キー: YoutubeLivechatMessage の id を参照
    message_id: Mapped[str] = mapped_column(
        ForeignKey("youtube_livechat_messages.id"),
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
    )
    # 占い対象かどうか
    is_target: Mapped[bool] = mapped_column(nullable=False)
    # 占いに必要な情報
    required_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=True)
    # 占い結果: text 型
    result: Mapped[str] = mapped_column(Text, default="", nullable=True)
    # 音声ファイルのパス
    result_voice_path: Mapped[str] = mapped_column(Text, default="", nullable=True)
    is_played: Mapped[bool] = mapped_column(nullable=False, default=False)

    def construct_from_entity(
        self,
    ):
        pass
