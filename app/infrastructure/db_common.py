import re
from datetime import datetime

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


# ヘルパー関数: CamelCase を snake_case に変換する
def camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TableNameMixin:
    @declared_attr
    def __tablename__(cls) -> str:
        # 例: "YoutubeLivechatMessage" -> "youtube_livechat_messages"
        return camel_to_snake(cls.__name__).replace("_orm", "") + "s"
