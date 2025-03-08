from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LocationEntity(BaseModel):
    """
    Location object containing latitude and longitude.
    """

    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")


class AstrologyResultEntity(BaseModel):
    """
    Astrology result object.
    """

    value: str = Field(..., description="Astrology result")
    is_ok: bool = Field(False, description="Whether an error occurred or not")


class InfoForAstrologyEntity(BaseModel):
    """
    Information required for astrology.

    Attributes:
        name (str): Name of the human.
        birthday (str): Birthday of the human in the format YYYY/MM/DD.
        birth_time (str): Birth time of the human in the format HH:MM.
        birthplace (str): Birthplace of the human.
        worries (str): Worries of the human.
    """

    name: str | None = Field(..., description="Name of the human. default is ``")
    birthday: str = Field(
        ..., description="Birthday of the human in the format YYYY/MM/DD"
    )
    birth_time: str = Field(
        ..., description="Birth time of the human in the format HH:MM. default is ''"
    )
    birthplace: str = Field(..., description="Birth place of the human. default is ``")

    worries: str = Field("", description="Worries of the human. default is ``")

    @classmethod
    @field_validator("birthday")
    def validate_birthday(cls, v):
        try:
            datetime.strptime(v, "%Y/%m/%d")
        except ValueError:
            raise ValueError("birthday must be in the format YYYY/MM/DD")
        return v

    @classmethod
    @field_validator("birth_time")
    def validate_birth_time(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("birth_time must be in the format HH:MM")
        return v

    def supplement_by_default(self):
        """
        Supplement the following fields with default values if they are empty.
        - birth_time: "00:00"
        - birthplace: "Tokyo"
        - worries: ""
        name and birthday are not supplemented.
        """
        if not self.birth_time:
            self.birth_time = "00:00"
        if not self.birthplace:
            self.birthplace = "Tokyo"
        if not self.worries:
            self.worries = ""

    def satisfied_all(self) -> bool:
        """
        Check if all the required fields are filled.
        """
        # check format
        try:
            self.validate_birthday(self.birthday)
            self.validate_birth_time(self.birth_time)
        except ValueError:
            return False
        return all([self.name, self.birthday, self.birth_time, self.birthplace])

    def __str__(self):
        return f"{self.name} ({self.birthday} {self.birth_time} {self.birthplace}), worries: {self.worries}"


class WesternAstrologyStatusEntity(BaseModel):
    """
    西洋占星術の結果を表すエンティティ
    """

    message_id: Any = Field(
        ..., description="message id"
    )  # TODO: youtubeだけでなく他の媒体におけるメッセージオブジェクトのIDも扱う
    is_target: bool = Field(
        ..., description="whether this status is target for astrology"
    )
    required_info: InfoForAstrologyEntity | None = Field(
        None, description="The base information to execute astrology"
    )
    result: str = Field("", description="The result of astrology")
    result_voice_path: str = Field(
        "", description="The path of voice file of the result"
    )
    is_played: bool = Field(
        False, description="Whether the result has been played or not"
    )
