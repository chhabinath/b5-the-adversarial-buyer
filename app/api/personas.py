"""Buyer persona API."""

from fastapi import APIRouter

from app.buyer.personas import list_personas
from app.schemas.personas import BuyerPersonaResponse


router = APIRouter(prefix="/api/v1/personas", tags=["personas"])


@router.get("", response_model=list[BuyerPersonaResponse])
async def get_personas() -> list[BuyerPersonaResponse]:
    """Return the available skeptical enterprise buyer personas."""

    return [
        BuyerPersonaResponse(
            name=persona.name,
            description=persona.description,
            concerns=list(persona.concerns),
            objection_categories=list(persona.objection_categories),
        )
        for persona in list_personas()
    ]