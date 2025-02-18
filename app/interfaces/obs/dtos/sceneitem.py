from pydantic import BaseModel, Field
from typing import Optional


class SceneItemTransform(BaseModel):
    alignment: int
    boundsAlignment: int
    boundsHeight: float
    boundsType: str
    boundsWidth: float
    cropBottom: int
    cropLeft: int
    cropRight: int
    cropToBounds: bool
    cropTop: int
    height: float
    positionX: float
    positionY: float
    rotation: float
    scaleX: float
    scaleY: float
    sourceHeight: float
    sourceWidth: float
    width: float


class SceneItem(BaseModel):
    inputKind: str
    isGroup: Optional[bool]
    sceneItemBlendMode: str
    sceneItemEnabled: bool
    sceneItemId: int
    sceneItemIndex: int
    sceneItemLocked: bool
    sceneItemTransform: SceneItemTransform
    sourceName: str
    sourceType: str
    sourceUuid: str


class Scene(BaseModel):
    sceneIndex: int
    sceneName: str
    sceneUuid: str


class SceneList(BaseModel):
    currentPreviewSceneName: Optional[str]
    currentPreviewSceneUuid: Optional[str]
    currentProgramSceneName: str
    currentProgramSceneUuid: str
    scenes: list[Scene]


# 使用例
if __name__ == "__main__":
    data = {
        'inputKind': 'text_ft2_source_v2',
        'isGroup': None,
        'sceneItemBlendMode': 'OBS_BLEND_NORMAL',
        'sceneItemEnabled': True,
        'sceneItemId': 6,
        'sceneItemIndex': 1,
        'sceneItemLocked': False,
        'sceneItemTransform': {
            'alignment': 5,
            'boundsAlignment': 0,
            'boundsHeight': 0.0,
            'boundsType': 'OBS_BOUNDS_NONE',
            'boundsWidth': 0.0,
            'cropBottom': 0,
            'cropLeft': 0,
            'cropRight': 0,
            'cropToBounds': False,
            'cropTop': 0,
            'height': 63.77777862548828,
            'positionX': 41.5,
            'positionY': 947.0,
            'rotation': 0.0,
            'scaleX': 0.3904411792755127,
            'scaleY': 0.3888888955116272,
            'sourceHeight': 164.0,
            'sourceWidth': 976.0,
            'width': 381.0705871582031
        },
        'sourceName': 'comment',
        'sourceType': 'OBS_SOURCE_TYPE_INPUT',
        'sourceUuid': '38c0c7eb-39a3-441b-b8d5-af1a42c91b81'
    }

    scene_item = SceneItem(**data)
    print(scene_item)
