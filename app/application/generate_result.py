from logging import getLogger

from app.application.audio import txt_to_audiofile
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
from app.infrastructure.repositoriesImpl import WesternAstrologyResultRepositoryImpl

logger = getLogger(__name__)


def prepare_for_astrology(
    astrology_repo: WesternAstrologyResultRepository,
    livechat_repo: YoutubeLiveChatMessageRepository,
) -> None:
    """
    コメント一覧から、占い対象のコメントを取得し、占いに必要な情報を抽出してDBに保存する
    """
    logger.info("Start preparing for astrology.")
    # まだ占い結果がない占星術ステータスを取得
    target_astrology_status_list: list[WesternAstrologyStatusEntity] = (
        astrology_repo.get_not_prepared_target(limit=3)
    )  # TODO limitは設定で変えるようにする

    # 占い結果がない占星術ステータスのメッセージIDを取得
    target_astrology_status_message_ids = [
        astrology_status.message_id for astrology_status in target_astrology_status_list
    ]
    # メッセージIDからメッセージを取得
    target_livechat_list: list[LiveChatMessageEntity] = (
        livechat_repo.get_by_message_ids(target_astrology_status_message_ids)
    )

    # メッセージから占星術に必要な情報を抽出する
    for astrology_status in target_astrology_status_list:
        target_livechat = [
            livechat
            for livechat in target_livechat_list
            if livechat.id == astrology_status.message_id
        ][0]
        info: InfoForAstrologyEntity = extract_info_for_astrology(
            _input=f"NAME:{target_livechat.authorDetails.displayName}, INFO:{target_livechat.snippet.displayMessage}"
        )
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
        f"Finished preparing for astrology. Prepared {len(target_astrology_status_list)} astrology statuses."
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

    # 占い結果を生成
    logger.info("Start generating astrology result list.")
    for astrology_status in target_astrology_status_list:
        required_info: InfoForAstrologyEntity = astrology_status.required_info

        if required_info.satisfied_all():
            logger.info(
                f"Required information is satisfied: (message_id={astrology_status.message_id})"
            )
            # LLMを使って占星術結果を取得
            prompt = create_prompt_for_astrology(
                name=required_info.name,
                birthday=required_info.birthday,
                birth_time=required_info.birth_time,
                birthplace=required_info.birthplace,
                worries=required_info.worries,
            )
            logger.info(
                f"start generating astrology result: (message_id={astrology_status.message_id})"
            )
            output: Output = get_output(
                prompt=prompt, temperature=0.9, top_k=40, max_output_tokens=1000
            )
            astrology_status.result = output.text
            logger.info(
                f"Succeeded to generate astrology result: (message_id={astrology_status.message_id})"
            )
            # 占い結果を保存
            astrology_repo.save([astrology_status])
        else:
            logger.info(
                f"Required information is not satisfied: (message_id={astrology_status.message_id})"
            )

    logger.info(
        f"Finished generating astrology result list. Generated {len(target_astrology_status_list)} astrology results."
    )


def result_to_voice(astrology_repo: WesternAstrologyResultRepository) -> None:
    """
    占い結果を音声化し、DBに保存する
    """
    # まだ音声化されていない占星術ステータスを取得
    target_astrology_status_list: list[WesternAstrologyStatusEntity] = (
        astrology_repo.get_no_voice_target(limit=1)
    )  # TODO limitは設定で変えるようにする

    # 占い結果を音声化
    logger.info("Start generating voice for astrology result list.")
    for astrology_status in target_astrology_status_list:
        result = astrology_status.result

        if result:
            logger.info(
                f"Start generating voice for astrology result: (message_id={astrology_status.message_id})"
            )
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
            except Exception as e:
                logger.error(
                    f"Failed to generate voice for astrology result: (message_id={astrology_status.message_id})"
                )
                raise e
        else:
            # get_no_voice_targetで結果が空ではないものを取得しているので、ここに来ることはないはず
            logger.error(
                f"No result to generate voice: (message_id={astrology_status.message_id})"
            )


def get_astrology_results_for_view(
    astrology_repo: WesternAstrologyResultRepository,
) -> tuple[list[WesternAstrologyStatusEntity], list[LiveChatMessageEntity]]:
    """
    画面で表示するための占星術結果を取得する
    """
    status_list, chat_message_list = (
        astrology_repo.get_all_prepared_status_and_message()
    )
    return status_list, chat_message_list
