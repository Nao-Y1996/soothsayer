from logging import getLogger
from typing import Literal, Type

import google.generativeai as genai
from pydantic import BaseModel
from pydantic_ai.models.gemini import _GeminiJsonSchema

from app.core.const import GEMINI_API_KEY
from app.infrastructure.external.llm.dtos import Output, StructuredOutput, Usage

logger = getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)


def get_structured_output(
    cls: Type[BaseModel],
    model_name: Literal[
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-2.0-flash-exp",
    ] = "gemini-1.5-flash",
    prompt: str = "",
    temperature: float = 0.5,
    top_k: int = 40,
    max_output_tokens: int = 1000,
) -> StructuredOutput:
    """
    get structured output from Google generative AI API

    Args:
        cls (Type[BaseModel]): pydantic model class the output should be validated against
        model_name (str): model name
        prompt (str, optional): prompt text. Defaults to "".
        temperature (float, optional): temperature. Defaults to 0.5.
        top_k (int, optional): top_k. Defaults to 40.
        max_output_tokens (int, optional): max_output_tokens. Defaults to 500.

    Returns:
        tuple[Usage, BaseModel]: usage and instance validated against the provided pydantic model class
    """
    model = genai.GenerativeModel(model_name)

    schema = _GeminiJsonSchema(cls.model_json_schema()).simplify()

    config = genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
        top_k=top_k,
        max_output_tokens=max_output_tokens,
    )
    result = model.generate_content(
        contents=prompt,
        generation_config=config,
        stream=False,
    )

    usage = result.usage_metadata
    val = StructuredOutput(
        model=cls.model_validate_json(result.text),
        usage=Usage(
            prompt_token=usage.prompt_token_count,
            response_token=usage.candidates_token_count,
        ),
    )
    return val


def get_output(
    model_name: Literal[
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-2.0-flash-exp",
    ] = "gemini-1.5-flash",
    prompt: str = "",
    temperature: float = 0.5,
    top_k: int = 40,
    max_output_tokens: int = 1000,
) -> Output:
    """
    get output from Google generative AI API

    Args:
        model_name (str): model name
        prompt (str, optional): prompt text. Defaults to "".
        temperature (float, optional): temperature. Defaults to 0.5.
        top_k (int, optional): top_k. Defaults to 40.
        max_output_tokens (int, optional): max_output_tokens. Defaults to 500.

    Returns:
        str: output text
    """
    model = genai.GenerativeModel(model_name)

    config = genai.GenerationConfig(
        response_mime_type="text/plain",
        temperature=temperature,
        top_k=top_k,
        max_output_tokens=max_output_tokens,
    )

    result = model.generate_content(
        contents=prompt,
        generation_config=config,
        stream=False,
    )

    return Output(
        text=result.text,
        usage=Usage(
            prompt_token=result.usage_metadata.prompt_token_count,
            response_token=result.usage_metadata.candidates_token_count,
        ),
    )


if __name__ == "__main__":
    from pydantic import BaseModel, Field

    from app.infrastructure.external.llm.utils import pydantic_to_markdown

    class Human(BaseModel):
        name: str = Field(..., description="Name of the human")
        age: int = Field(..., description="Age of the human")

    system_prompt = """
extract human information
{model_description}
    """.format(
        model_description=pydantic_to_markdown(Human)
    )
    user_prompt = "My name is John Doe. I am software engineer. I am 30 years old."
    print(system_prompt)

    structured_output: StructuredOutput = get_structured_output(
        cls=Human,
        model_name="gemini-1.5-flash",
        prompt=system_prompt + "\n\n" + user_prompt,
    )
    logger.info(structured_output.model)
    print(structured_output.usage)
    logger.info(structured_output.usage)
    print(structured_output.usage)

    logger.info("---------------")

    output: Output = get_output(
        model_name="gemini-1.5-flash",
        prompt=system_prompt + "\n\n" + user_prompt,
    )
    logger.info(output.text)
    print(output.text)
    logger.info(output.usage)
    print(output.usage)
