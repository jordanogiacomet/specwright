from initializer.engine.archetype_engine import (
    canonical_archetype_id,
    detect_archetype as detect_canonical_archetype,
)
from initializer.flow.archetype_detection import (
    detect_archetype as detect_flow_archetype,
)


def test_regression_flow_and_canonical_detectors_match_for_editorial_prompt():
    prompt = "Editorial CMS with admin panel and public website"

    canonical = detect_canonical_archetype(prompt)
    flow = detect_flow_archetype(prompt)

    assert flow == canonical
    assert flow["id"] == "editorial-cms"
    assert flow["name"] == "editorial-cms"


def test_regression_flow_and_canonical_detectors_match_for_marketplace_prompt():
    prompt = "Marketplace for courses with reviews and payments"

    canonical = detect_canonical_archetype(prompt)
    flow = detect_flow_archetype(prompt)

    assert flow == canonical
    assert flow["id"] == "marketplace"
    assert flow["name"] == "marketplace"


def test_regression_flow_and_canonical_detectors_match_for_saas_prompt():
    prompt = "SaaS analytics dashboard for teams"

    canonical = detect_canonical_archetype(prompt)
    flow = detect_flow_archetype(prompt)

    assert flow == canonical
    assert flow["id"] == "saas-app"
    assert flow["name"] == "saas-app"


def test_regression_flow_and_canonical_detectors_match_for_fallback_prompt():
    prompt = "Simple website for a local business"

    canonical = detect_canonical_archetype(prompt)
    flow = detect_flow_archetype(prompt)

    assert flow == canonical
    assert flow["id"] == "generic-web-app"
    assert flow["name"] == "generic-web-app"


def test_regression_canonical_archetype_id_normalizes_aliases():
    assert canonical_archetype_id("api-service") == "generic-web-app"
    assert canonical_archetype_id({"id": "api-service"}) == "generic-web-app"
    assert canonical_archetype_id({"name": "api-service"}) == "generic-web-app"