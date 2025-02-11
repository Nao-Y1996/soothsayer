import json
from logging import getLogger
from typing import Any, Type, cast

from pydantic import BaseModel
from redis import ConnectionPool, Redis
from redis.asyncio import ConnectionPool as AsyncConnectionPool
from redis.asyncio import Redis as AsyncRedis
from src.const.value import REDIS_DB, REDIS_HOST, REDIS_PORT
from src.database.kvstore import KVStore

logger = getLogger(__name__)


class RedisStore(KVStore):
    def __init__(self) -> None:
        # --- 同期版の設定 ---
        self._sync_pool = ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,  # 文字列で取得できるようにする
        )
        self.sync_client = Redis(connection_pool=self._sync_pool)

        # --- 非同期版の設定 ---
        self._async_pool = AsyncConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )
        self.async_client = AsyncRedis(connection_pool=self._async_pool)

        # check if the connection is successful. if not, raise an error
        try:
            self.sync_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            raise ValueError(f"Failed to connect to Redis: {e}")

    # ------------------------------
    # 同期版メソッド
    # ------------------------------

    def set_model(self, key: str, model: BaseModel) -> None:
        """
        Pydanticモデルのデータ（JSON文字列）を同期で保存する
        """
        json_value = model.model_dump_json()
        self.sync_client.set(key, json_value)

    def get_model(
        self, key: str, model_type: Type[BaseModel] | None = None
    ) -> BaseModel | dict[str, Any]:
        """
        同期で保存されたJSON文字列を取得し、必要に応じてモデルに検証する
        """
        raw_value = cast(str, self.sync_client.get(key))
        json_value: dict[str, Any] = json.loads(raw_value)
        if model_type:
            return model_type.model_validate(json_value)
        return json_value

    def get_keys(self) -> list[str]:
        """
        同期でキー一覧を取得する
        """
        return cast(list[str], self.sync_client.keys())

    def delete_key(self, key: str) -> None:
        """
        同期でキーを削除する
        """
        self.sync_client.delete(key)

    # ------------------------------
    # 非同期版メソッド
    # ------------------------------

    async def async_set_model(self, key: str, model: BaseModel) -> None:
        """
        Pydanticモデルのデータ（JSON文字列）を非同期で保存する
        """
        json_value = model.model_dump_json()
        await self.async_client.set(key, json_value)

    async def async_get_model(
        self, key: str, model_type: Type[BaseModel] | None = None
    ) -> BaseModel | dict[str, Any]:
        """
        非同期で保存されたJSON文字列を取得し、必要に応じてモデルに検証する
        """
        raw_value = await self.async_client.get(key)
        if raw_value is None:
            return {}
        json_value: dict[str, Any] = json.loads(raw_value)
        if model_type:
            return model_type.model_validate(json_value)
        return json_value

    async def async_get_keys(self) -> list[str]:
        """
        非同期でキー一覧を取得する
        """
        keys = await self.async_client.keys()
        return keys

    async def async_delete_key(self, key: str) -> None:
        """
        非同期でキーを削除する
        """
        await self.async_client.delete(key)


# モジュールレベルのグローバル変数として RedisStore のインスタンスを作成
redis_store = RedisStore()
