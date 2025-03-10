import time
from logging import getLogger

from app.application.audio import txt_to_audiofile
from app.application.thread_manager import ThreadTask
from app.application.westernastrology import (
    create_prompt_for_astrology,
    extract_info_for_astrology,
)
from app.core.const import AUDIO_DIR
from app.domain.repositories import (
    WesternAstrologyResultRepository,
    YoutubeLiveChatMessageRepository,
)
from app.domain.westernastrology import (
    InfoForAstrologyEntity,
    WesternAstrologyStatusEntity,
)
from app.domain.youtube.live import LiveChatMessageEntity
from app.infrastructure.external.llm.dtos import Output
from app.infrastructure.external.llm.llm_google import get_output
from app.infrastructure.repositoriesImpl import (
    WesternAstrologyResultRepositoryImpl,
    YoutubeLiveChatMessageRepositoryImpl,
)

logger = getLogger(__name__)


def prepare_for_astrology(
    astrology_repo: WesternAstrologyResultRepository,
    livechat_repo: YoutubeLiveChatMessageRepository,
) -> None:
    """
    コメント一覧から、占い対象のコメントを取得し、占いに必要な情報を抽出してDBに保存する
    """
    # まだ占い結果がない占星術ステータスを取得
    target_astrology_status_list: list[WesternAstrologyStatusEntity] = (
        astrology_repo.get_not_prepared_target(limit=3)
    )  # TODO limitは設定で変えるようにする
    if not target_astrology_status_list:
        return

    # 占い結果がない占星術ステータスのメッセージIDを取得
    target_astrology_status_message_ids = [
        astrology_status.message_id for astrology_status in target_astrology_status_list
    ]
    # メッセージIDからメッセージを取得
    target_livechat_list: list[LiveChatMessageEntity] = (
        livechat_repo.get_by_message_ids(target_astrology_status_message_ids)
    )

    logger.info(
        "Start preparing for astrology. message_ids: {target_astrology_status_message_ids}"
    )
    # メッセージから占星術に必要な情報を抽出する
    for astrology_status in target_astrology_status_list:
        target_livechat = [
            livechat
            for livechat in target_livechat_list
            if livechat.id == astrology_status.message_id
        ][0]
        info: InfoForAstrologyEntity = extract_info_for_astrology(
            name=target_livechat.authorDetails.displayName,
            _input=target_livechat.snippet.displayMessage,
        )
        # 不足情報を補完
        info.supplement_by_default()
        # 必要情報が正しいフォーマットで揃っているか確認
        if info.satisfied_all():
            astrology_status.required_info = info
        else:
            logger.info(
                f"Required information is not satisfied: (message_id={astrology_status.message_id})"
            )
            # 必要な情報が揃っていない場合は、占い対象から外す
            astrology_status.is_target = False

    astrology_repo.save(target_astrology_status_list)
    logger.info(
        f"Finished preparing for astrology. Prepared {len(target_astrology_status_list)} astrology statuses. message_ids: {target_astrology_status_message_ids}"
    )


def generate_astrology_result(
    astrology_repo: WesternAstrologyResultRepositoryImpl,
) -> None:
    """
    占い対象のコメントから占い結果を生成し、DBに保存する
    """
    # まだ占い結果がない占星術ステータスを取得
    target_astrology_status_list: list[WesternAstrologyStatusEntity] = (
        astrology_repo.get_prepared_target_with_no_result(limit=3)
    )  # TODO limitは設定で変えるようにする
    message_ids = [_status.message_id for _status in target_astrology_status_list]
    if not message_ids:
        return

    # 占い結果を生成
    logger.info(f"Start generating astrology result list. message_ids: {message_ids}")
    for astrology_status in target_astrology_status_list:
        required_info: InfoForAstrologyEntity = astrology_status.required_info

        logger.info(
            f"start generating astrology result: (message_id={astrology_status.message_id})"
        )
        if required_info.satisfied_all():
            try:
                # LLMを使って占星術結果を取得
                prompt = create_prompt_for_astrology(
                    name=required_info.name,
                    birthday=required_info.birthday,
                    birth_time=required_info.birth_time,
                    birthplace=required_info.birthplace,
                    worries=required_info.worries,
                )
                output: Output = get_output(
                    prompt=prompt, temperature=0.9, top_k=40, max_output_tokens=1000
                )
            except Exception as e:
                logger.exception(
                    f"Failed to generate astrology result. (message_id={astrology_status.message_id})"
                )
                # FIXME: 失敗した対象をそのままにすると、次以降の占い結果生成でも失敗し続ける可能性がある
                continue
            astrology_status.result = output.text
            logger.info(
                f"Succeeded to generate astrology result: (message_id={astrology_status.message_id})"
            )
            # 占い結果を保存
            astrology_repo.save([astrology_status])
        else:
            logger.info(
                f"Failed to generate astrology result. Required information is not satisfied: (message_id={astrology_status.message_id})"
            )

    logger.info(
        f"Finished generating astrology result list. Generated {len(target_astrology_status_list)} astrology results. (message_ids: {message_ids})"
    )


def result_to_voice(astrology_repo: WesternAstrologyResultRepository) -> None:
    """
    占い結果を音声化し、DBに保存する
    """
    # まだ音声化されていない占星術ステータスを取得
    target_astrology_status_list: list[WesternAstrologyStatusEntity] = (
        astrology_repo.get_no_voice_target(limit=1)
    )  # TODO limitは設定で変えるようにする
    if not target_astrology_status_list:
        return

    # 占い結果を音声化
    logger.info("Start generating voice for astrology result list.")
    for astrology_status in target_astrology_status_list:
        result = astrology_status.result

        logger.info(
            f"Start generating voice for astrology result: (message_id={astrology_status.message_id})"
        )
        if result:
            # 音声化
            try:
                audio_file_path = txt_to_audiofile(
                    text=result,
                    audiofile_path=AUDIO_DIR / f"{astrology_status.message_id}.wav",
                )
                astrology_status.result_voice_path = audio_file_path
                logger.info(
                    f"Succeeded to generate voice for astrology result: (message_id={astrology_status.message_id})"
                )
                # 音声化結果を保存
                # 生成は1つ1つが時間がかかるので、1つの結果を生成したらすぐに保存する
                astrology_repo.save([astrology_status])
            except IOError as e:
                logger.exception(
                    f"Failed to generate voice for astrology result: (message_id={astrology_status.message_id})"
                )
                raise e
        else:
            # get_no_voice_targetで結果が空ではないものを取得しているので、ここに来ることはないはず
            logger.exception(
                f"No result to generate voice: (message_id={astrology_status.message_id})"
            )


class GenerateResultTask(ThreadTask):

    def run(self):
        """占星術結果生成の無限ループ処理"""
        livechat_repo = YoutubeLiveChatMessageRepositoryImpl()
        astrology_repo = WesternAstrologyResultRepositoryImpl()
        logger.info("Start Thread for generating result.")
        while not self.stop_event.is_set():
            try:
                # 占いの準備
                prepare_for_astrology(astrology_repo, livechat_repo)
                # 占い結果の生成
                generate_astrology_result(astrology_repo)
                # 停止フラグのチェック間隔として sleep
                time.sleep(1)
            except Exception as e:
                logger.exception("Failed to generate result: " + str(e))
        logger.info("Stopped Thread for generating result.")


result_thread_task = GenerateResultTask("result")
