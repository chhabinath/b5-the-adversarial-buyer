"""API schemas for buyer personas."""

from pydantic import BaseModel


class BuyerPersonaResponse(BaseModel):
    name: str
    description: str
    concerns: list[str]
    objection_categories: list[str]