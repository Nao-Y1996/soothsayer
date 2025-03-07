from logging import getLogger
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_, select

from app.domain.repositories import (
    WesternAstrologyResultRepository,
    YoutubeLiveChatMessageRepository,
)
from app.domain.westernastrology import (
    InfoForAstrologyEntity,
    WesternAstrologyStatusEntity,
)
from app.domain.youtube.live import LiveChatMessageEntity
from app.infrastructure.tables import (
    WesternAstrologyStatusOrm,
    YoutubeLivechatMessageOrm,
)

logger = getLogger(__name__)


class YoutubeLiveChatMessageRepositoryImpl(YoutubeLiveChatMessageRepository):

    def __init__(self, session: Session):
        self.session: Session = session

    def save(self, messages: list[LiveChatMessageEntity]) -> None:
        """
        メッセージリストをDBに保存または更新する。
        コメントIDに重複がある場合は、on_conflict_do_update で更新する。
        """
        if not messages:
            logger.debug("messages is empty.")
            return

        message_dict_list = [message.model_dump() for message in messages]

        # INSERT ... ON CONFLICT DO NOTHING (UPSERT)
        for message_dict in message_dict_list:
            logger.debug(f"message_dict: {message_dict}")
            logger.debug(f"message_dict['id']: {message_dict['id']}")
        stm = (
            pg_insert(YoutubeLivechatMessageOrm)
            .values(
                [
                    {"id": d.get("id", str(uuid4())), "message": d}
                    for d in message_dict_list
                ]
            )
            .on_conflict_do_nothing(
                index_elements=["id"]
            )  # id がユニークキーであることを前提
            # sqlalchemyのバージョン2系 スタイルでは、ORMクラスそのものではなく
            # 「返して欲しいカラム」を returning(...) で列挙することが推奨されている
            # 例えばテーブル全カラムを返すなら __table__ を指定。
            .returning(YoutubeLivechatMessageOrm.__table__)
        )
        logger.debug(f"stm: {stm}")
        result = self.session.execute(stm)
        self.session.commit()
        logger.debug(f"result: {result}")

    def get_by_message_ids(self, message_ids: list[str]) -> list[LiveChatMessageEntity]:
        if not message_ids:
            return []

        # JSONカラムの特定キーを文字列として取り出し、in_ 句で検索する
        stmt = select(YoutubeLivechatMessageOrm).where(
            YoutubeLivechatMessageOrm.message["id"].astext.in_(message_ids)
        )
        rows = self.session.execute(stmt).scalars().all()

        # 取得した行からエンティティに変換して返す
        results: list[LiveChatMessageEntity] = []
        for row in rows:
            entity = LiveChatMessageEntity(**row.message)
            results.append(entity)

        return results


class WesternAstrologyResultRepositoryImpl(WesternAstrologyResultRepository):

    def __init__(self, session: Session):
        self.session: Session = session

    def save(self, status_list: list[WesternAstrologyStatusEntity]) -> None:
        """
        占い結果をDBに保存または更新する。
        """
        values = [
            {
                "message_id": str(status.message_id),
                "is_target": status.is_target,
                "required_info": status.required_info.model_dump(),
                "result": status.result,
                "result_voice_path": status.result_voice_path,
                "is_played": status.is_played,
            }
            for status in status_list
        ]
        if not values:
            # valuesが[]の時にはWesternAstrologyStatusOrmのフィールドが全て空のデータをinsertしようとして
            # message_idのnot null制約(primary key)に引っかかるため、ここでreturnする
            return
        stmt = pg_insert(WesternAstrologyStatusOrm).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["message_id"],
            set_={
                # "message_id": stmt.excluded.message_id,
                "is_target": stmt.excluded.is_target,
                "required_info": stmt.excluded.required_info,
                "result": stmt.excluded.result,
                "result_voice_path": stmt.excluded.result_voice_path,
                "is_played": stmt.excluded.is_played,
            },
        )
        self.session.execute(stmt)
        self.session.commit()

    def get_not_prepared_target(self, limit: int) -> list[WesternAstrologyStatusEntity]:
        stmt = (
            select(WesternAstrologyStatusOrm)
            .where(
                and_(
                    WesternAstrologyStatusOrm.is_target == True,  # noqa: E712
                    WesternAstrologyStatusOrm.required_info == {},
                    WesternAstrologyStatusOrm.result == "",
                )
            )
            .join(
                YoutubeLivechatMessageOrm,
                YoutubeLivechatMessageOrm.id == WesternAstrologyStatusOrm.message_id,
            )
            .order_by(YoutubeLivechatMessageOrm.created_at)
            .limit(limit)
        )

        orm_objects = self.session.execute(stmt).scalars().all()
        return [
            WesternAstrologyStatusEntity(
                message_id=obj.message_id,
                is_target=obj.is_target,
                required_info=None,
                result=obj.result,
                result_voice_path=obj.result_voice_path,
                is_played=obj.is_played,
            )
            for obj in orm_objects
        ]

    def get_all_prepared_status_and_message(
        self,
    ) -> tuple[list[WesternAstrologyStatusEntity], list[LiveChatMessageEntity]]:
        stmt = (
            select(WesternAstrologyStatusOrm, YoutubeLivechatMessageOrm)
            .where(
                and_(
                    WesternAstrologyStatusOrm.is_target == True,  # noqa: E712
                    WesternAstrologyStatusOrm.required_info != {},
                )
            )
            .join(
                YoutubeLivechatMessageOrm,
                YoutubeLivechatMessageOrm.id == WesternAstrologyStatusOrm.message_id,
            )
            .order_by(YoutubeLivechatMessageOrm.created_at)
        )
        # scalars().all()だと複数のオブジェクトのうち最初のオブジェクトしかが返ってこない
        # このケースだと、WesternAstrologyStatusOrmしか取得できない
        orm_objects = self.session.execute(stmt).all()
        # そのため、scalars()は使用せずにall()で全てのオブジェクトを取得する必要がある
        status_entities: list[WesternAstrologyStatusEntity] = []
        livechat_messages: list[LiveChatMessageEntity] = []

        for status_obj, livechat_obj in orm_objects:
            status_entity = WesternAstrologyStatusEntity(
                message_id=status_obj.message_id,
                is_target=status_obj.is_target,
                required_info=InfoForAstrologyEntity(**status_obj.required_info),
                result=status_obj.result,
                result_voice_path=status_obj.result_voice_path,
                is_played=status_obj.is_played,
            )
            status_entities.append(status_entity)
            livechat_messages.append(LiveChatMessageEntity(**livechat_obj.message))

        return status_entities, livechat_messages

    def get_prepared_target_with_no_result(
        self, limit: int
    ) -> list[WesternAstrologyStatusEntity]:
        stmt = (
            select(WesternAstrologyStatusOrm)
            .where(
                and_(
                    WesternAstrologyStatusOrm.is_target == True,  # noqa: E712
                    WesternAstrologyStatusOrm.required_info != {},
                    WesternAstrologyStatusOrm.result == "",
                )
            )
            .join(
                YoutubeLivechatMessageOrm,
                YoutubeLivechatMessageOrm.id == WesternAstrologyStatusOrm.message_id,
            )
            .order_by(YoutubeLivechatMessageOrm.created_at)
            .limit(limit)
        )
        orm_objects = self.session.execute(stmt).scalars().all()
        return [
            WesternAstrologyStatusEntity(
                message_id=obj.message_id,
                is_target=obj.is_target,
                required_info=InfoForAstrologyEntity(**obj.required_info),
                result=obj.result,
                result_voice_path=obj.result_voice_path,
                is_played=obj.is_played,
            )
            for obj in orm_objects
        ]

    def get_no_voice_target(self, limit: int) -> list[WesternAstrologyStatusEntity]:
        stmt = (
            select(WesternAstrologyStatusOrm)
            .where(
                and_(
                    WesternAstrologyStatusOrm.is_target == True,  # noqa: E712
                    WesternAstrologyStatusOrm.required_info != {},
                    WesternAstrologyStatusOrm.result != "",
                    WesternAstrologyStatusOrm.result_voice_path == "",
                )
            )
            .join(
                YoutubeLivechatMessageOrm,
                YoutubeLivechatMessageOrm.id == WesternAstrologyStatusOrm.message_id,
            )
            .order_by(YoutubeLivechatMessageOrm.created_at)
            .limit(limit)
        )
        orm_objects = self.session.execute(stmt).scalars().all()
        return [
            WesternAstrologyStatusEntity(
                message_id=obj.message_id,
                is_target=obj.is_target,
                required_info=InfoForAstrologyEntity(**obj.required_info),
                result=obj.result,
                result_voice_path=obj.result_voice_path,
                is_played=obj.is_played,
            )
            for obj in orm_objects
        ]

    def get_all_with_voice(self) -> list[WesternAstrologyStatusEntity]:
        stmt = (
            select(WesternAstrologyStatusOrm)
            .where(
                and_(
                    WesternAstrologyStatusOrm.is_target == True,  # noqa: E712
                    WesternAstrologyStatusOrm.required_info != {},
                    WesternAstrologyStatusOrm.result != "",
                    WesternAstrologyStatusOrm.result_voice_path != "",
                )
            )
            .join(
                YoutubeLivechatMessageOrm,
                YoutubeLivechatMessageOrm.id == WesternAstrologyStatusOrm.message_id,
            )
            .order_by(YoutubeLivechatMessageOrm.created_at)
        )
        orm_objects = self.session.execute(stmt).scalars().all()
        return [
            WesternAstrologyStatusEntity(
                message_id=obj.message_id,
                is_target=obj.is_target,
                required_info=InfoForAstrologyEntity(**obj.required_info),
                result=obj.result,
                result_voice_path=obj.result_voice_path,
                is_played=obj.is_played,
            )
            for obj in orm_objects
        ]

    def add_initial(self, chat_ids: list[str], is_target_list: list[bool]) -> None:
        """
        未処理の占い結果をDBに保存する。
        """
        if len(chat_ids) != len(is_target_list):
            raise ValueError("chat_ids and is_target_list must have the same length.")

        values = [
            {
                "message_id": chat_id,
                "is_target": is_target,
                "required_info": {},
                "is_played": False,
            }
            for chat_id, is_target in zip(chat_ids, is_target_list, strict=True)
        ]
        if not values:
            return
            # valuesが[]の時にはWesternAstrologyStatusOrmのフィールドが全て空のデータをinsertしようとして
            # message_idのnot null制約(primary key)に引っかかるため、ここでreturnする
        stmt = (
            pg_insert(WesternAstrologyStatusOrm)
            .values(values)
            .on_conflict_do_nothing(
                index_elements=[WesternAstrologyStatusOrm.message_id]
            )
        )
        self.session.execute(stmt)
        self.session.commit()
