"""Structured skeptical enterprise buyer personas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuyerPersona:
    name: str
    description: str
    concerns: tuple[str, ...]
    objection_categories: tuple[str, ...]


PERSONAS: tuple[BuyerPersona, ...] = (
    BuyerPersona(
        name="CFO",
        description="Challenges whether the commercial case is financially defensible.",
        concerns=("ROI", "pricing", "hidden costs", "contract commitments", "scalability", "unclear economics"),
        objection_categories=("pricing", "cost predictability", "ROI", "commercial risk"),
    ),
    BuyerPersona(
        name="CTO",
        description="Challenges the technical architecture, scale, and long-term platform risk.",
        concerns=("architecture", "scalability", "reliability", "APIs", "integrations", "vendor lock-in", "technical limitations"),
        objection_categories=("architecture", "reliability", "scalability", "platform risk"),
    ),
    BuyerPersona(
        name="Security",
        description="Challenges whether the product can pass security and compliance review.",
        concerns=("SOC 2", "ISO 27001", "GDPR", "encryption", "SSO", "access control", "data retention", "security documentation"),
        objection_categories=("compliance", "data protection", "identity and access", "security assurance"),
    ),
    BuyerPersona(
        name="Procurement",
        description="Challenges commercial terms, supplier risk, and contractual obligations.",
        concerns=("pricing", "contract terms", "cancellation", "SLA", "vendor risk", "minimum commitment"),
        objection_categories=("contract terms", "supplier risk", "SLA", "procurement process"),
    ),
    BuyerPersona(
        name="Engineering",
        description="Challenges implementation effort, integration quality, and developer constraints.",
        concerns=("API", "SDK", "documentation", "integration complexity", "rate limits", "migration", "implementation effort"),
        objection_categories=("integration", "developer experience", "migration", "operational effort"),
    ),
)


def list_personas() -> tuple[BuyerPersona, ...]:
    """Return personas in stable deterministic order."""

    return PERSONAS


def get_persona(name: str) -> BuyerPersona | None:
    """Find a persona by case-insensitive name."""

    normalized_name = name.strip().lower()
    return next((persona for persona in PERSONAS if persona.name.lower() == normalized_name), None)