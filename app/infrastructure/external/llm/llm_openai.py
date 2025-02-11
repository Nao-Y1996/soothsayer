from logging import getLogger
from typing import Literal, Type

from openai import OpenAI
from pydantic import BaseModel

from app.core.const import OPENAI_API_KEY
from app.infrastructure.external.llm.llm_interface import (
    Output,
    StructuredOutput,
    Usage,
)

logger = getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)


def get_structured_output(
    cls: Type[BaseModel],
    model_name: Literal[
        "o1-2024-12-17",
        "o1-mini",
        "o1-mini-2024-09-12",
        "gpt-4o",
        "gpt-4o-2024-11-20",
        "gpt-4o-2024-08-06",
        "gpt-4o-2024-05-13",
        "chatgpt-4o-latest",
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
    ] = "gpt-4o-2024-08-06",
    system_prompt: str = "",
    user_prompt: str = "",
) -> StructuredOutput:
    """
    get structured output from OpenAI API
    Args:
        cls: (Type[BaseModel]): pydantic model class the output should be validated against
        model_name: (str): model name
        system_prompt: (str): system prompt. Defaults to "".
        user_prompt: (str): user prompt. Defaults to "".

    Returns:
        tuple[Usage, BaseModel]: usage and instance validated against the provided pydantic model class
    """
    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=cls,
    )

    return StructuredOutput(
        model=completion.choices[0].message.parsed,
        usage=Usage(
            prompt_token=completion.usage.prompt_tokens,
            response_token=completion.usage.completion_tokens,
        ),
    )


def get_output(
    model_name: Literal[
        "o1-2024-12-17",
        "o1-mini",
        "o1-mini-2024-09-12",
        "gpt-4o",
        "gpt-4o-2024-11-20",
        "gpt-4o-2024-08-06",
        "gpt-4o-2024-05-13",
        "chatgpt-4o-latest",
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
    ] = "gpt-4o-2024-08-06",
    system_prompt: str = "",
    user_prompt: str = "",
) -> Output:
    """
    get basic output from OpenAI API
    Args:
        model_name: (str): model name
        system_prompt: (str): system prompt. Defaults to "".
        user_prompt: (str): user prompt. Defaults to "".

    Returns:
        tuple[Usage, BaseModel]: usage and instance validated against the provided pydantic model class
    """
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "developer", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    return Output(
        text=completion.choices[0].message.content,
        usage=Usage(
            prompt_token=completion.usage.prompt_tokens,
            response_token=completion.usage.completion_tokens,
        ),
    )


if __name__ == "__main__":
    from pprint import pprint

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

    structured_output: StructuredOutput = get_structured_output(
        cls=Human,
        model_name="gpt-4o-2024-08-06",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    pprint(structured_output.model)
    logger.info(structured_output.usage)

    logger.info("---------------")

    output: Output = get_output(
        model_name="gpt-4o-2024-08-06",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    logger.info(output.text)
    logger.info(output.usage)
