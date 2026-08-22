from fastapi.testclient import TestClient

from app.buyer.personas import get_persona, list_personas
from app.main import app


def test_personas_include_five_buyer_roles() -> None:
    assert [persona.name for persona in list_personas()] == [
        "CFO",
        "CTO",
        "Security",
        "Procurement",
        "Engineering",
    ]
    assert get_persona("security").concerns[0] == "SOC 2"


def test_personas_endpoint_returns_structured_personas() -> None:
    response = TestClient(app).get("/api/v1/personas")

    assert response.status_code == 200
    assert len(response.json()) == 5
    assert response.json()[4]["name"] == "Engineering"