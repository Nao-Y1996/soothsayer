import functools
from logging import getLogger

from obswebsocket import obsws
from obswebsocket import requests as obs_requests

from app.config import (
    COMMENT_FILE_PATH,
    OBS_HOST,
    OBS_PASSWORD,
    OBS_PORT,
    USER_NAME_FILE_PATH,
)
from app.interfaces.obs.dtos.sceneitem import SceneItem, SceneItemTransform, SceneList

logger = getLogger(__name__)


def auto_connect(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Start {func.__name__}")

        # 第一引数にwsが存在し、かつNoneでなければ再利用
        if args and isinstance(args[0], obsws) and args[0] is not None:
            return func(*args, **kwargs)
        else:
            # wsが渡されていない場合は新たに作成・接続
            ws = obsws(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD)
            ws.connect()
            logger.info("Connected to OBS")
            try:
                # 第一引数としてwsを渡す
                return func(ws, *args, **kwargs)
            finally:
                ws.disconnect()
                logger.info("Disconnected from OBS")

    return wrapper


@auto_connect
def get_scene_list(ws: obsws) -> SceneList:
    response = ws.call(obs_requests.GetSceneList())
    scene_list: SceneList = SceneList(**response.datain)
    return scene_list


@auto_connect
def get_scene_item_id_by_name(ws: obsws, scene_name: str, source_name: str):
    logger.info(f"{scene_name=}, {source_name=}")
    scene_items: list[SceneItem] = get_scene_items(ws, scene_name)
    scene_item = [
        scene_item for scene_item in scene_items if scene_item.sourceName == source_name
    ]
    scene_item_id = scene_item[0].sceneItemId if scene_item else None
    if scene_item_id is None:
        raise Exception(f"Source not found: {source_name}")
    return scene_item_id


@auto_connect
def get_scene_items(ws: obsws, scene_name: str) -> list[SceneItem]:
    logger.info(f"{scene_name=}")
    result = ws.call(obs_requests.GetSceneItemList(sceneName=scene_name))
    if not result.status:
        raise Exception(f"{result.datain}")
    scene_items: list[dict] = result.datain["sceneItems"]
    logger.info(f"{scene_items=}")
    scene_items: list[SceneItem] = [
        SceneItem(**scene_item) for scene_item in scene_items
    ]
    return scene_items


@auto_connect
def set_scene_item_transform(
    ws: obsws, scene_name: str, scene_item_id: int, transform: SceneItemTransform
):
    logger.info(f"{scene_name=}, {scene_item_id=}, {transform=}")
    result = ws.call(
        obs_requests.SetSceneItemTransform(
            sceneName=scene_name,
            sceneItemId=scene_item_id,
            sceneItemTransform=transform.model_dump(),
        )
    )
    if not result.status:
        raise Exception(f"{result.datain}")


@auto_connect
def set_scene_item_enabled(
    ws: obsws, scene_name: str, scene_item_id: int, enabled: bool
):
    logger.info(f"{scene_name=}, {scene_item_id=}, {enabled=}")
    result = ws.call(
        obs_requests.SetSceneItemEnabled(
            sceneName=scene_name, sceneItemId=scene_item_id, sceneItemEnabled=enabled
        )
    )
    if not result.status:
        raise Exception(f"Failed to set scene item enabled: {result.datain}, ")


def update_user_name(user_name: str):
    logger.info(f"{user_name=}")
    try:
        with open(USER_NAME_FILE_PATH, mode="w", encoding="utf-8") as f:
            f.write(user_name)
    except Exception as e:
        logger.exception(f"Failed to update username: {e}")
        raise e


def update_comment(comment: str):
    logger.info(f"{comment=}")
    try:
        with open(COMMENT_FILE_PATH, mode="w", encoding="utf-8") as f:
            f.write(comment)
    except Exception as e:
        logger.exception(f"Failed to update comment: {e}")
        raise e


def get_user_name() -> str:
    try:
        with open(USER_NAME_FILE_PATH, mode="r", encoding="utf-8") as f:
            user_name = f.read()
    except Exception as e:
        logger.exception(f"Failed to get username: {e}")
        raise e
    return user_name


def get_comment() -> str:
    try:
        with open(COMMENT_FILE_PATH, mode="r", encoding="utf-8") as f:
            comment = f.read()
    except Exception as e:
        logger.exception(f"Failed to get comment: {e}")
        raise e
    return comment


@auto_connect
def main(ws: obsws):
    scene_list: SceneList = get_scene_list(ws)
    scene_name = scene_list.currentProgramSceneName
    if scene_name == "サンプルシーン":

        # シーン内のアイテム一覧を取得
        scene_items: list[SceneItem] = get_scene_items(ws, scene_name)
        for scene_item in scene_items:

            if scene_item.sourceName == "username":

                # 位置を変更
                scene_item.sceneItemTransform.positionX = 0.0
                scene_item.sceneItemTransform.positionY = 300.0
                set_scene_item_transform(
                    ws,
                    scene_name,
                    scene_item.sceneItemId,
                    scene_item.sceneItemTransform,
                )

                # 表示/非表示を切り替え
                set_scene_item_enabled(
                    ws,
                    scene_name,
                    scene_item.sceneItemId,
                    enabled=(not scene_item.sceneItemEnabled),
                )


if __name__ == "__main__":
    main()
