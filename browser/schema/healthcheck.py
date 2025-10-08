from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """
    Health Check response model.
    """

    status: str = Field(..., description="The status of the service")

    class Config:
        from_attributes = True
        populate_by_name = True
