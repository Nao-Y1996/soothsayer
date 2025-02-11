from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Union

from pydantic import BaseModel


class KVStore(ABC):
    @abstractmethod
    def set_model(self, key: str, model: BaseModel) -> None:
        """
        Pydanticモデルのデータを同期で保存する
        """
        raise ValueError("Not implemented: set_model")

    @abstractmethod
    def get_model(
        self, key: str, model_type: Type[BaseModel] | None = None
    ) -> Union[BaseModel, Dict[str, Any]]:
        """
        同期でデータを取得する。
        model_type が指定されている場合は、検証済みのモデルインスタンスとして返す
        """
        raise ValueError("Not implemented: get_json")

    @abstractmethod
    def get_keys(self) -> List[str]:
        """
        同期でキー一覧を取得する
        """
        raise ValueError("Not implemented: get_keys")

    @abstractmethod
    def delete_key(self, key: str) -> None:
        """
        同期でキーを削除する
        """
        raise ValueError("Not implemented: delete_key")

    # ------------------------------
    # 非同期版のメソッド
    # ------------------------------
    @abstractmethod
    async def async_set_model(self, key: str, model: BaseModel) -> None:
        """
        Pydanticモデルのデータを非同期で保存する
        """
        raise ValueError("Not implemented: async_set_model")

    @abstractmethod
    async def async_get_model(
        self, key: str, model_type: Type[BaseModel] | None = None
    ) -> Union[BaseModel, Dict[str, Any]]:
        """
        非同期でデータを取得する。
        model_type が指定されている場合は、検証済みのモデルインスタンスとして返す
        """
        raise ValueError("Not implemented: async_get_json")

    @abstractmethod
    async def async_get_keys(self) -> List[str]:
        """
        非同期でキー一覧を取得する
        """
        raise ValueError("Not implemented: async_get_keys")

    @abstractmethod
    async def async_delete_key(self, key: str) -> None:
        """
        非同期でキーを削除する
        """
        raise ValueError("Not implemented: async_delete_key")
