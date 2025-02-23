from logging import getLogger

from app.application.westernastrology import extract_info_for_astrology,setup_swiss_ephemeris, setup_dir,create_prompt_for_astrology

logger = getLogger(__name__)

if __name__ == "__main__":
    from app.infrastructure.external.llm.llm_google import get_output as gemini

    human_info = extract_info_for_astrology(
        "太郎です。2000年の12月3日の午後7時に東京で生まれです"
        # "太郎です。2000年の12月3日の午後7時に東京で生まれです。お昼にたべらケーキが美味しかった！でも最近忙しすぎ..."
    )
    if not human_info.satisfied_all():
        raise ValueError("failed to extract all the required information.")
    logger.info(f"Extracted information: {human_info}")

    setup_swiss_ephemeris(setup_dir)

    prompt = create_prompt_for_astrology(
        human_info.name,
        human_info.birthday,
        human_info.birth_time,
        human_info.birthplace,
        human_info.worries,
    )
    output = gemini(prompt=prompt, temperature=0.9, top_k=40, max_output_tokens=1000)
    logger.info(output.text)
    logger.info(f"\ntoken usage: {output.usage}")
