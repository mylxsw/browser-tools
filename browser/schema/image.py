from pydantic import BaseModel, Field


class ImageResponse(BaseModel):
    """
    Image response model.
    """

    image_base64: str = Field(..., description="The base64 encoded image")
    image_type: str = Field(..., description="The image type: png, jpg, etc.")

    class Config:
        from_attributes = True
        populate_by_name = True


class TextResponse(BaseModel):
    """
    Text response model.
    """

    text: str = Field(..., description="The text")

    class Config:
        from_attributes = True
        populate_by_name = True


class TokenUsage(BaseModel):
    """
    Token usage model.
    """

    total_tokens: int = Field(..., description="The total tokens")
    input_tokens: int = Field(..., description="The prompt tokens")
    output_tokens: int = Field(..., description="The completion tokens")
    cached_tokens: int = Field(..., description="The cached tokens")
    model: str = Field(..., description="The model")

    class Config:
        from_attributes = True
        populate_by_name = True


class TextWithTokenUsageResponse(BaseModel):
    """
    Text response model with token usage.
    """

    text: str = Field(..., description="The text")
    token_usage: TokenUsage = Field(..., description="The token usages")

    class Config:
        from_attributes = True
        populate_by_name = True
