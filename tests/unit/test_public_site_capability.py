"""Tests for public-site capability handler.

Validates the renamed static asset delivery story and its criteria.
"""

from initializer.capabilities.public_site import apply_public_site


def _make_spec(needs_public_site=None, primary_audience=None):
    spec = {"discovery": {"decision_signals": {}}}
    if needs_public_site is not None:
        spec["discovery"]["decision_signals"]["needs_public_site"] = needs_public_site
    if primary_audience is not None:
        spec["discovery"]["decision_signals"]["primary_audience"] = primary_audience
    return spec


def test_static_delivery_story_title():
    spec = _make_spec(needs_public_site=True)
    arch = {"decisions": [], "components": []}
    _, stories = apply_public_site(spec, arch, [])
    assert any(s["title"] == "Configure static asset delivery" for s in stories)


def test_static_delivery_has_story_key():
    spec = _make_spec(needs_public_site=True)
    arch = {"decisions": [], "components": []}
    _, stories = apply_public_site(spec, arch, [])
    story = next(s for s in stories if s["title"] == "Configure static asset delivery")
    assert story["story_key"] == "infra.static-delivery"


def test_static_delivery_no_external_cdn():
    spec = _make_spec(needs_public_site=True)
    arch = {"decisions": [], "components": []}
    _, stories = apply_public_site(spec, arch, [])
    story = next(s for s in stories if s["title"] == "Configure static asset delivery")
    boundaries = " ".join(story["scope_boundaries"])
    assert "Cloudflare" in boundaries or "external CDN" in boundaries.lower()


def test_static_delivery_mentions_next_image():
    spec = _make_spec(needs_public_site=True)
    arch = {"decisions": [], "components": []}
    _, stories = apply_public_site(spec, arch, [])
    story = next(s for s in stories if s["title"] == "Configure static asset delivery")
    criteria = " ".join(story["acceptance_criteria"])
    assert "Image" in criteria


def test_old_cdn_title_deduplication():
    """If a story titled 'Configure CDN' already exists, don't add another."""
    spec = _make_spec(needs_public_site=True)
    arch = {"decisions": [], "components": []}
    existing = [{"title": "Configure CDN", "id": "ST-099"}]
    _, stories = apply_public_site(spec, arch, existing)
    assert len(stories) == 1
    assert stories[0]["title"] == "Configure CDN"
