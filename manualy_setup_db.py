from sqlalchemy import create_engine

if __name__ == "__main__":

    from app.core.const import PG_URL
    from app.infrastructure import (
        tables,
    )  # テーブル定義をここで読み込まないとalembicがテーブルを作成できない
    from app.infrastructure.db_common import Base

    print(tables)

    engine = create_engine(PG_URL, echo=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine, checkfirst=False)
