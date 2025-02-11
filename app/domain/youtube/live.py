from typing import Any, List, Optional, Type, Union

from pydantic import BaseModel, field_validator

from app.core.utils import SerializableDatetime


# -------------------------------
# 各種サブモデル
# -------------------------------
class TextMessageDetailsEntity(BaseModel):
    messageText: Optional[str] = None


class FanFundingEventDetailsEntity(BaseModel):
    amountMicros: Optional[int] = None
    currency: Optional[str] = None
    amountDisplayStringEntity: Optional[str] = None
    userComment: Optional[str] = None


class MessageDeletedDetailsEntity(BaseModel):
    deletedMessageId: Optional[str] = None


class BannedUserDetailsEntity(BaseModel):
    channelId: Optional[str] = None
    channelUrl: Optional[str] = None
    displayName: Optional[str] = None
    profileImageUrl: Optional[str] = None


class UserBannedDetailsEntity(BaseModel):
    bannedUserDetails: Optional[BannedUserDetailsEntity] = None
    banType: Optional[str] = None
    banDurationSeconds: Optional[int] = None


class MemberMilestoneChatDetailsEntity(BaseModel):
    userComment: Optional[str] = None
    memberMonth: Optional[int] = None
    memberLevelName: Optional[str] = None


class NewSponsorDetailsEntity(BaseModel):
    memberLevelName: Optional[str] = None
    isUpgrade: Optional[bool] = None


class SuperChatDetailsEntity(BaseModel):
    amountMicros: Optional[int] = None
    currency: Optional[str] = None
    amountDisplayString: Optional[str] = None
    userComment: Optional[str] = None
    tier: Optional[int] = None


class SuperStickerMetadataEntity(BaseModel):
    stickerId: Optional[str] = None
    altText: Optional[str] = None
    language: Optional[str] = None


class SuperStickerDetailsEntity(BaseModel):
    superStickerMetadata: Optional[SuperStickerMetadataEntity] = None
    amountMicros: Optional[int] = None
    currency: Optional[str] = None
    amountDisplayString: Optional[str] = None
    tier: Optional[int] = None


class PollOptionEntity(BaseModel):
    optionText: Optional[str] = None
    tally: Optional[str] = None


class PollMetadataEntity(BaseModel):
    options: Optional[List[PollOptionEntity]] = None
    questionText: Optional[str] = None
    status: Optional[str] = None  # enum想定


class PollDetailsEntity(BaseModel):
    metadata: Optional[PollMetadataEntity] = None


class MembershipGiftingDetailsEntity(BaseModel):
    giftMembershipsCount: Optional[int] = None
    giftMembershipsLevelName: Optional[str] = None


class GiftMembershipReceivedDetailsEntity(BaseModel):
    memberLevelName: Optional[str] = None
    gifterChannelId: Optional[str] = None
    associatedMembershipGiftingMessageId: Optional[str] = None


class SnippetEntity(BaseModel):
    type_: Optional[str] = None
    liveChatId: Optional[str] = None
    authorChannelId: Optional[str] = None
    publishedAt: Optional[SerializableDatetime] = None
    hasDisplayContent: Optional[bool] = None
    displayMessage: Optional[str] = None
    fanFundingEventDetails: Optional[FanFundingEventDetailsEntity] = None
    textMessageDetails: Optional[TextMessageDetailsEntity] = None
    messageDeletedDetails: Optional[MessageDeletedDetailsEntity] = None
    userBannedDetails: Optional[UserBannedDetailsEntity] = None
    memberMilestoneChatDetails: Optional[MemberMilestoneChatDetailsEntity] = None
    newSponsorDetails: Optional[NewSponsorDetailsEntity] = None
    superChatDetails: Optional[SuperChatDetailsEntity] = None
    superStickerDetails: Optional[SuperStickerDetailsEntity] = None
    pollDetails: Optional[PollDetailsEntity] = None
    membershipGiftingDetails: Optional[MembershipGiftingDetailsEntity] = None
    giftMembershipReceivedDetails: Optional[GiftMembershipReceivedDetailsEntity] = None


class AuthorDetailsEntity(BaseModel):
    channelId: Optional[str] = None
    channelUrl: Optional[str] = None
    displayName: Optional[str] = None
    profileImageUrl: Optional[str] = None
    isVerified: Optional[bool] = None
    isChatOwner: Optional[bool] = None
    isChatSponsor: Optional[bool] = None
    isChatModerator: Optional[bool] = None


# -------------------------------
# ルートモデル
# -------------------------------
class LiveChatMessageEntity(BaseModel):
    """
    https://developers.google.com/youtube/v3/live/docs/liveChatMessages
    """

    kind: Optional[str] = None
    etag: Optional[str] = None
    id: Optional[str] = None  # ← YouTubeが付与するID
    snippet: Optional[SnippetEntity] = None
    authorDetails: Optional[AuthorDetailsEntity] = None

    @field_validator("id")
    def name_to_lower(cls, v: str):
        return v.replace(".", "")

    @classmethod
    def _get_field_names(cls, model: Type[BaseModel], prefix: str = "") -> List[str]:
        """
        指定したモデルのフィールド名を再帰的に取得します。
        """
        fields = []

        for name, annotation in model.__annotations__.items():
            # JSON変換する時使う名前を取得
            # アノテーションに紐づくフィールド情報を取得
            field_info = model.model_fields.get(name)
            if field_info:
                # フィールド情報からエイリアス（別名）を取得。エイリアスがない場合はフィールド名を使用
                json_name = field_info.alias or name
            else:
                # フィールド情報がない場合、アノテーションの名前をそのまま使用
                json_name = name

            current_path = f"{prefix}.{json_name}" if prefix else json_name

            # `annotation`を型ヒントから型情報として取り出す
            # 例: Optional[str] -> str
            origin_type = getattr(annotation, "__origin__", None)

            # annotationがOptional[X]の場合、Xを取り出す
            if origin_type is Union:
                # 型引数リストを取得
                type_args = getattr(annotation, "__args__", ())
                # NoneTypeを除外した型を取得
                non_none_types = [arg for arg in type_args if arg is not type(None)]
                if len(non_none_types) == 1:
                    annotation = non_none_types[0]
                    origin_type = getattr(annotation, "__origin__", None)
                elif len(non_none_types) > 1:
                    # Union[type1, type2 ... , None] のようなケース
                    # 複数の型の型アノテーションを持つ場合、現時点では型を特定できないのでstrとして扱う
                    # 将来的に改善の余地あり
                    fields.append(current_path)
                    continue

            # リストの型の場合
            if origin_type is list:
                # リストの要素の型を取得
                inner_type = annotation.__args__[0]

                # リストの中身がBaseModelを継承しているならさらに展開する
                if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                    fields.extend(cls._get_field_names(inner_type, current_path))
                else:
                    fields.append(current_path)

            # BaseModelを継承した型の場合
            elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
                fields.extend(cls._get_field_names(annotation, current_path))
            else:
                fields.append(current_path)
        return fields

    @classmethod
    def csv_headers(cls) -> List[str]:
        """
        フィールド名を再帰的に取得し、CSVのヘッダーとして使用できる形式で返します。
        """
        return cls._get_field_names(cls)

    @classmethod
    def column_names(cls) -> Any:
        """ """
        return [header.replace(".", "_") for header in cls.csv_headers()]

    def _get_attr_by_path(self, path: List[str]) -> Any:
        """
        属性名をドットで繋いだリストを辿って値を取得します。
        """
        attr: LiveChatMessageEntity | None = self
        for name in path:
            if attr is None:
                return None

            if isinstance(attr, list):
                try:
                    if name.isdigit():
                        attr = attr[int(name)]
                    else:
                        attr_list = []
                        for a in attr:
                            try:
                                # `getattr`ではなく辞書アクセスの要領で取得
                                attr_list.append(a.__dict__[name])
                            except KeyError:
                                pass
                        attr = ",".join([str(a) for a in attr_list if a is not None])
                except (IndexError, KeyError):
                    attr = None
            else:
                try:
                    attr = attr.__dict__[name]
                except KeyError:
                    attr = None
        return attr

    def to_csv_row(self) -> List[str]:
        """
        CSV出力用に、csv_headers() が返す項目の順番に従って値を取得しリスト化します。
        """
        headers = self.csv_headers()
        values = []

        for h in headers:
            attr_value = self._get_attr_by_path(h.split("."))
            if attr_value is None:
                values.append("")
            else:
                values.append(str(attr_value))
        return values


if __name__ == "__main__":
    print(LiveChatMessageEntity.column_names())
