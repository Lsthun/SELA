from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

import requests


PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAILS_URL = "https://places.googleapis.com/v1/{resource_name}"
DEFAULT_SOURCE_URL = "https://www.google.com/search?q=sela+construction"
CACHE_TTL = timedelta(minutes=30)
ASSET_ROOT = "assets"

_CACHE_LOCK = Lock()
_CACHE: dict[tuple[str, str, str], tuple[datetime, dict[str, Any]]] = {}

SITE = {
    "name": "Sela Construction, LLC",
    "eyebrow": "Louisiana and Mississippi Gulf Coast",
    "phone_display": "(504) 460-1717",
    "phone_href": "tel:+15044601717",
    "email": "tgiarrusso@sela-construction.com",
    "email_href": "mailto:tgiarrusso@sela-construction.com",
    "location": "Diamondhead, MS 39525",
    "hours": "Monday - Friday · 8:00 AM - 5:00 PM",
    "quote_href": "mailto:tgiarrusso@sela-construction.com?subject=Residential%20Project%20Inquiry",
    "logo_asset": f"{ASSET_ROOT}/logo.png",
    "hero_image_asset": f"{ASSET_ROOT}/hero-exterior.jpg",
    "service_area_asset": f"{ASSET_ROOT}/gulf-coast-states.svg",
    "license_copy": "Licensed for residential and commercial construction in Louisiana and Mississippi.",
}

TRUST_POINTS = [
    {
        "title": "Since 2005",
        "description": "More than 20 years of hands-on project delivery across the Gulf Coast.",
    },
    {
        "title": "Management On Site",
        "description": "A small-team build model keeps communication direct from walkthrough to punch list.",
    },
    {
        "title": "LA + MS Licensed",
        "description": "Residential work is backed by active licensing in both service areas.",
    },
]

SERVICES = [
    {
        "title": "Kitchen and Bath Renovations",
        "description": "Rework the rooms that take the most daily wear with sharper layouts, durable materials, and better finish coordination.",
    },
    {
        "title": "Whole-Home Remodeling",
        "description": "Coordinate structural updates, finish selections, and trade sequencing without losing sight of how the home needs to function.",
    },
    {
        "title": "Additions and Ground-Up Builds",
        "description": "Expand the footprint or start from scratch with one team managing schedule, scope, and site flow.",
    },
    {
        "title": "Custom Cabinets and Finish Work",
        "description": "Bring storage, trim, and built-ins into the same visual language as the rest of the remodel.",
    },
]

PROJECTS = [
    {
        "title": "Bright, hardworking interiors",
        "description": "Residential spaces shaped around better circulation, layered light, and material choices that stay calm over time.",
        "image_asset": f"{ASSET_ROOT}/project-interior.jpg",
        "image_alt": "Interior residential renovation with layered lighting and natural finishes",
    },
    {
        "title": "Detailed finish packages",
        "description": "Cabinetry, trim, and paint scopes that feel coordinated instead of added on at the end.",
        "image_asset": f"{ASSET_ROOT}/project-finish.jpg",
        "image_alt": "Finished residential room with custom trim and cabinetry details",
    },
    {
        "title": "A warm first impression",
        "description": "Street-facing updates and entry sequences that raise curb appeal without feeling disconnected from the house.",
        "image_asset": f"{ASSET_ROOT}/project-curb-appeal.jpg",
        "image_alt": "Residential exterior showing a polished home entry and curb appeal improvements",
    },
]

PROCESS_STEPS = [
    {
        "step": "01",
        "title": "Walk the home",
        "description": "Start with the actual constraints: layout pain points, finish goals, site conditions, and budget priorities.",
    },
    {
        "step": "02",
        "title": "Align scope and pricing",
        "description": "Define what changes, what stays, and how the work should sequence before the house gets opened up.",
    },
    {
        "step": "03",
        "title": "Build with steady communication",
        "description": "Keep homeowners informed with direct contact, visible site leadership, and a disciplined closeout.",
    },
]

QUICK_LINKS = [
    {"label": "Services", "href": "#services"},
    {"label": "Residential Work", "href": "#work"},
    {"label": "Process", "href": "#process"},
    {"label": "Reviews", "href": "#reviews"},
    {"label": "Contact", "href": "#contact"},
]


def build_home_context(
    *,
    google_places_api_key: str | None,
    google_place_query: str,
    google_place_id: str | None,
) -> dict[str, Any]:
    review_feed = get_five_star_reviews(
        api_key=google_places_api_key,
        text_query=google_place_query,
        place_id=google_place_id,
    )
    marquee_reviews = _build_review_marquee(review_feed.get("reviews") or [])
    return {
        "site": SITE,
        "trust_points": TRUST_POINTS,
        "services": SERVICES,
        "projects": PROJECTS,
        "process_steps": PROCESS_STEPS,
        "quick_links": QUICK_LINKS,
        "review_feed": review_feed,
        "review_marquee_items": marquee_reviews,
    }


def get_five_star_reviews(
    *,
    api_key: str | None,
    text_query: str,
    place_id: str | None = None,
    max_reviews: int = 5,
) -> dict[str, Any]:
    if not api_key:
        return _empty_feed(
            status="config_missing",
            description="Add GOOGLE_PLACES_API_KEY to .env to load live 5-star Google reviews through Places.",
        )

    normalized_place_id = _normalize_place_id(place_id)
    cache_key = (api_key, text_query, normalized_place_id or "")
    now = datetime.now(UTC)

    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

    try:
        with requests.Session() as session:
            place = _resolve_place(
                session=session,
                api_key=api_key,
                text_query=text_query,
                normalized_place_id=normalized_place_id,
            )
            if not place:
                feed = _empty_feed(
                    status="place_not_found",
                    description="Google Places could not resolve the SELA listing from the configured query.",
                )
            else:
                feed = _load_place_review_feed(
                    session=session,
                    api_key=api_key,
                    place=place,
                    max_reviews=max_reviews,
                )
    except requests.RequestException:
        feed = _empty_feed(
            status="request_failed",
            description="Google Places could not be reached right now. The page will keep working without the live review feed.",
        )

    with _CACHE_LOCK:
        _CACHE[cache_key] = (now + CACHE_TTL, feed)

    return feed


def _resolve_place(
    *,
    session: requests.Session,
    api_key: str,
    text_query: str,
    normalized_place_id: str | None,
) -> dict[str, Any] | None:
    if normalized_place_id:
        return {
            "id": normalized_place_id,
            "name": f"places/{normalized_place_id}",
            "displayName": {"text": "Sela Construction, LLC"},
            "formattedAddress": "Diamondhead, MS 39525",
        }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.name,places.displayName,places.formattedAddress",
    }
    response = session.post(
        PLACES_SEARCH_URL,
        headers=headers,
        json={"textQuery": text_query},
        timeout=12,
    )
    response.raise_for_status()
    places = response.json().get("places") or []
    return places[0] if places else None


def _load_place_review_feed(
    *,
    session: requests.Session,
    api_key: str,
    place: dict[str, Any],
    max_reviews: int,
) -> dict[str, Any]:
    resource_name = place["name"]
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "id,name,displayName,formattedAddress,rating,userRatingCount,reviews",
    }
    response = session.get(
        PLACES_DETAILS_URL.format(resource_name=resource_name),
        headers=headers,
        timeout=12,
    )
    response.raise_for_status()
    details = response.json()

    reviews: list[dict[str, Any]] = []
    for raw_review in details.get("reviews") or []:
        rating = int(raw_review.get("rating") or 0)
        if rating != 5:
            continue
        review_text = _review_text(raw_review)
        if not review_text:
            continue
        reviews.append(
            {
                "author": ((raw_review.get("authorAttribution") or {}).get("displayName") or "Google reviewer").strip(),
                "rating": rating,
                "text": review_text,
                "relative_time": (raw_review.get("relativePublishTimeDescription") or "").strip(),
                "publish_time": raw_review.get("publishTime") or "",
            }
        )
        if len(reviews) >= max_reviews:
            break

    place_id_value = (details.get("id") or place.get("id") or "").strip()
    rating = details.get("rating")
    user_rating_count = details.get("userRatingCount")

    if reviews:
        description = "Showing 5-star homeowner feedback pulled live from Google Places."
        status = "ready"
    else:
        description = "Google Places resolved the SELA listing, but no 5-star review snippets were returned in the current response."
        status = "no_five_star_reviews"

    return {
        "status": status,
        "description": description,
        "place_name": ((details.get("displayName") or {}).get("text") or (place.get("displayName") or {}).get("text") or "Sela Construction, LLC").strip(),
        "formatted_address": (details.get("formattedAddress") or place.get("formattedAddress") or "Diamondhead, MS 39525").strip(),
        "rating": rating,
        "rating_display": f"{float(rating):.1f}" if rating is not None else None,
        "user_rating_count": user_rating_count,
        "reviews": reviews,
        "source_url": _source_url(place_id_value),
        "source_label": "See Google profile",
    }


def _build_review_marquee(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not reviews:
        return []
    marquee_reviews = list(reviews)
    while len(marquee_reviews) < 4:
        marquee_reviews.extend(reviews)
    return marquee_reviews * 2


def _empty_feed(*, status: str, description: str) -> dict[str, Any]:
    return {
        "status": status,
        "description": description,
        "place_name": "Google Reviews",
        "formatted_address": "",
        "rating": None,
        "rating_display": None,
        "user_rating_count": None,
        "reviews": [],
        "source_url": DEFAULT_SOURCE_URL,
        "source_label": "Open Google listing",
    }


def _normalize_place_id(place_id: str | None) -> str | None:
    if not place_id:
        return None
    normalized = place_id.strip()
    if normalized.startswith("places/"):
        normalized = normalized.split("/", 1)[1]
    return normalized or None


def _review_text(review: dict[str, Any]) -> str:
    original_text = ((review.get("originalText") or {}).get("text") or "").strip()
    if original_text:
        return original_text
    return ((review.get("text") or {}).get("text") or "").strip()


def _source_url(place_id: str) -> str:
    if not place_id:
        return DEFAULT_SOURCE_URL
    return f"https://www.google.com/maps/search/?api=1&query_place_id={place_id}"
