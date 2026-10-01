"""FR-04, FR-05: Gemma output parsing and normalisation."""

import json

import pytest

from app.listing import FALLBACK_BACKGROUND, MAX_TITLE, ListingParseError, parse_listing

GOOD = {
    "product_name": "Water Bottle",
    "category": "Sports",
    "title": "Insulated Steel Water Bottle 750 ml",
    "description": "Keeps drinks cold for 24 hours.",
    "features": ["Double wall", "Leak proof", "BPA free"],
    "tags": ["bottle", "steel", "gym"],
    "alt_text": "A blue steel water bottle.",
    "social_caption": "Stay hydrated #gym",
    "background_hex": "#1a2b3c",
}


def test_parses_json_inside_code_fence():
    listing = parse_listing(f"```json\n{json.dumps(GOOD)}\n```")
    assert listing.product_name == "Water Bottle"
    assert listing.background_hex == "#1A2B3C"


def test_parses_json_surrounded_by_prose():
    listing = parse_listing(f"Sure! Here is the listing:\n{json.dumps(GOOD)}\nHope it helps.")
    assert listing.title == GOOD["title"]


def test_title_is_truncated():
    listing = parse_listing(json.dumps({**GOOD, "title": "Very long title " * 20}))
    assert len(listing.title) <= MAX_TITLE


def test_tags_are_cleaned_deduplicated_and_limited():
    tags = ["#Bottle", "bottle", "STEEL!", " gym ", *[f"tag{i}" for i in range(20)]]
    listing = parse_listing(json.dumps({**GOOD, "tags": tags}))
    assert listing.tags[:3] == ["bottle", "steel", "gym"]
    assert len(listing.tags) == 10
    assert len(set(listing.tags)) == len(listing.tags)


def test_too_few_tags_are_padded_to_minimum():
    listing = parse_listing(json.dumps({**GOOD, "tags": ["bottle"]}))
    assert len(listing.tags) >= 3


def test_comma_separated_tags_string_is_accepted():
    listing = parse_listing(json.dumps({**GOOD, "tags": "a, b, c, d"}))
    assert listing.tags == ["a", "b", "c", "d"]


@pytest.mark.parametrize("features", [[], ["one"], ["1", "2", "3", "4", "5"]])
def test_features_always_exactly_three(features):
    assert len(parse_listing(json.dumps({**GOOD, "features": features})).features) == 3


@pytest.mark.parametrize("value, expected", [
    ("#abcdef", "#ABCDEF"), ("abcdef", "#ABCDEF"), ("red", FALLBACK_BACKGROUND),
    ("#123", FALLBACK_BACKGROUND), (None, FALLBACK_BACKGROUND),
])
def test_background_hex_validation(value, expected):
    assert parse_listing(json.dumps({**GOOD, "background_hex": value})).background_hex == expected


def test_missing_fields_get_defaults():
    listing = parse_listing('{"title": "Mug"}')
    assert listing.title == "Mug"
    assert listing.alt_text
    assert len(listing.features) == 3


@pytest.mark.parametrize("text", ["", "   ", "no json here", "[1, 2, 3]", "{broken"])
def test_unusable_output_raises(text):
    with pytest.raises(ListingParseError):
        parse_listing(text)
