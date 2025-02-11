from pydantic import BaseModel, Field


class Usage(BaseModel):

    prompt_token: int = Field(
        ..., description="The number of tokens used in the prompt"
    )
    response_token: int = Field(
        ..., description="The number of tokens used in the response"
    )

    @property
    def total_tokens(self):
        return self.prompt_token + self.response_token

    def __str__(self):
        return f"Prompt token: {self.prompt_token}, Response token: {self.response_token}, Total tokens: {self.total_tokens}"


class StructuredOutput(BaseModel):
    """
    A structured output from an AI model
    """

    model: BaseModel = Field(..., description="The structured output from the AI model")
    usage: Usage = Field(..., description="Usage metadata of the AI model")


class Output(BaseModel):
    """
    An output from an AI model
    """

    text: str = Field(..., description="The output from the AI model")
    usage: Usage = Field(..., description="Usage metadata of the AI model")
