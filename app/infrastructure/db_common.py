import re
from datetime import datetime
from logging import getLogger

from sqlalchemy import TIMESTAMP, create_engine, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    sessionmaker,
)

from app.core.const import PG_URL

logger = getLogger(__name__)

engine = create_engine(PG_URL, echo=False, pool_size=10, max_overflow=5)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def initialize_db():
    from app.infrastructure import (
        tables,
    )  # テーブル定義をここで読み込まないとalembicがテーブルを作成できない
    print(tables)

    try:
        logger.info("Strat initializing DB")
        engine = create_engine(PG_URL, echo=True)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine, checkfirst=False)
        logger.info("Successfully initialized DB")
    except Exception as e:
        logger.exception(f"Failed to initialize DB: {e}")
