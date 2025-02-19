from pathlib import Path
from logging import getLogger

from obswebsocket import requests as obs_requests
from obswebsocket import obsws

from app.core.const import ROOT
from app.interfaces.obs.dtos.sceneitem import SceneItem, SceneList, SceneItemTransform

logger = getLogger(__name__)

HOST = "localhost"
PORT = 4455
PASSWORD = "1ApID1tERz9JiFQu"

user_name_file_path =  Path(ROOT) / "app" / "interfaces" / "obs" / "texts" / "username.txt"
comment_file_path =  Path(ROOT) / "app" / "interfaces" / "obs" / "texts" / "comment.txt"


def get_scene_list(ws: obsws) -> SceneList:
    response = ws.call(obs_requests.GetSceneList())
    scene_list: SceneList = SceneList(**response.datain)
    return scene_list


def get_scene_items(ws: obsws, scene_name: str) -> list[SceneItem]:
    result = ws.call(obs_requests.GetSceneItemList(sceneName=scene_name))
    if not result.status:
        raise Exception(f"Failed to get scene items: {result.datain}")
    scene_items: list[dict] = result.datain["sceneItems"]
    scene_items: list[SceneItem] = [SceneItem(**scene_item) for scene_item in scene_items]
    return scene_items


def set_scene_item_transform(ws: obsws, scene_name: str, scene_item_id: int, transform: SceneItemTransform):
    result = ws.call(obs_requests.SetSceneItemTransform(
        sceneName=scene_name,
        sceneItemId=scene_item_id,
        sceneItemTransform=transform.model_dump()
    ))
    if not result.status:
        raise Exception(f"Failed to set scene item transform: {result.datain}")


def set_scene_item_enabled(ws: obsws, scene_name: str, scene_item_id: int, enabled: bool):
    result = ws.call(obs_requests.SetSceneItemEnabled(
        sceneName=scene_name,
        sceneItemId=scene_item_id,
        sceneItemEnabled=enabled
    ))
    if not result.status:
        raise Exception(f"Failed to set scene item enabled: {result.datain}")


def update_user_name(user_name: str):
    try:
        with open(user_name_file_path, mode="w") as f:
            f.write(user_name)
    except Exception as e:
        logger.error(f"Failed to update username: {e}")
        raise e

def update_comment(comment: str):
    try:
        with open(comment_file_path, mode="w") as f:
            f.write(comment)
    except Exception as e:
        logger.error(f"Failed to update comment: {e}")
        raise e

def get_user_name() -> str:
    try:
        with open(user_name_file_path, mode="r") as f:
            user_name = f.read()
    except Exception as e:
        logger.error(f"Failed to get username: {e}")
        raise e
    return user_name

def get_comment() -> str:
    try:
        with open(comment_file_path, mode="r") as f:
            comment = f.read()
    except Exception as e:
        logger.error(f"Failed to get comment: {e}")
        raise e
    return comment


def main():
    ws = obsws(host=HOST, port=PORT, password=PASSWORD)
    ws.connect()

    try:

        # シーンの一覧を取得
        scene_list: SceneList = get_scene_list(ws)
        scene_name = scene_list.currentProgramSceneName
        if scene_name == "サンプルシーン":

            # シーン内のアイテム一覧を取得
            scene_items: list[SceneItem] = get_scene_items(ws, scene_name)
            for scene_item in scene_items:

                if scene_item.sourceName == "username":

                    # 位置を変更
                    scene_item.sceneItemTransform.positionX = 0.0
                    scene_item.sceneItemTransform.positionY = 0.0
                    set_scene_item_transform(
                        ws,
                        scene_name,
                        scene_item.sceneItemId,
                        scene_item.sceneItemTransform
                    )

                    # 表示/非表示を切り替え
                    set_scene_item_enabled(
                        ws,
                        scene_name,
                        scene_item.sceneItemId,
                        enabled=(not scene_item.sceneItemEnabled)
                    )

    finally:
        # 接続解除
        ws.disconnect()

if __name__ == "__main__":
    main()
