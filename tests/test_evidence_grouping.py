from uuid import uuid4

from app.extraction.evidence_grouping import group_evidence
from app.models.evidence import Evidence


def test_groups_feature_with_nearby_limit_and_pricing_evidence() -> None:
    page_id = uuid4()
    rows = [
        Evidence(
            id=uuid4(),
            page_id=page_id,
            section="Compute",
            text="Fluid Active CPU",
            element_type="feature",
            position=10,
        ),
        Evidence(
            id=uuid4(),
            page_id=page_id,
            section="Compute",
            text="4 hours / month included",
            element_type="limit",
            position=11,
        ),
        Evidence(
            id=uuid4(),
            page_id=page_id,
            section="Compute",
            text="Starting at $0.128 per hour",
            element_type="pricing",
            position=12,
        ),
    ]

    groups = group_evidence(rows)

    assert len(groups) == 1
    assert groups[0].feature == "Fluid Active CPU"
    assert groups[0].limit == "4 hours / month included"
    assert groups[0].pricing == "Starting at $0.128 per hour"
    assert {row.id for row in groups[0].evidence} == {row.id for row in rows}


def test_groups_firewall_rate_limit_without_replacing_raw_rows() -> None:
    page_id = uuid4()
    feature = Evidence(
        id=uuid4(),
        page_id=page_id,
        section="Firewall",
        text="Firewall Rate Limit Requests",
        element_type="feature",
        position=2,
    )
    limit = Evidence(
        id=uuid4(),
        page_id=page_id,
        section="Firewall",
        text="1M allowed requests / month included",
        element_type="limit",
        position=3,
    )
    pricing = Evidence(
        id=uuid4(),
        page_id=page_id,
        section="Firewall",
        text="Starting at $0.50 per 1M allowed requests",
        element_type="pricing",
        position=4,
    )

    groups = group_evidence([feature, limit, pricing])

    assert groups[0].section == "Firewall"
    assert groups[0].limit == limit.text
    assert groups[0].pricing == pricing.text
    assert feature in groups[0].evidence