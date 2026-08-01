"""
Parses a Google Maps Timeline export (Timeline.json / location-history.json)
into a flat list of dicts ready to build TimelineEntry rows from.

Confirmed against a real on-device export (2026-08): the file is a bare
JSON *array* of segments (not wrapped in a top-level object), and each
segment is one of three shapes:

  {"startTime": "...", "endTime": "...",
   "visit": {"topCandidate": {"placeID": "...", "semanticType": "Home",
                               "placeLocation": "geo:-33.90,18.69"},
             "probability": "0.94"}}

  {"startTime": "...", "endTime": "...",
   "activity": {"distanceMeters": "16696.585938",
                "start": "geo:-34.02,18.59", "end": "geo:-33.90,18.69",
                "topCandidate": {"type": "in passenger vehicle"}}}

  {"startTime": "...", "endTime": "...",
   "timelinePath": [{"point": "geo:...", "durationMinutesOffsetFromStartTime": "34"}]}

`timelinePath` segments are raw breadcrumb points, not a visit or a drive,
and are ignored.

Three things worth knowing:
  - Numbers (distanceMeters, probability) are encoded as *strings*, not
    JSON numbers.
  - Visits never carry a human-readable name or address — only a place ID,
    a semantic type ("Home"/"Work"/"Unknown") and coordinates. Google
    resolves the friendly name client-side in the Timeline app UI, but the
    exported file doesn't include it, so location_name/address are left
    for the user to fill in on the dashboard (semanticType is used as a
    starting hint when it's not "Unknown").
  - Visits can be nested: a broad "hierarchyLevel": "0" visit sometimes
    contains an overlapping "hierarchyLevel": "1" sub-visit at a different
    placeID (e.g. a specific shop inside a shopping centre). Only level "0"
    is imported — the Timeline app's own daily list doesn't surface the
    nested ones either, and importing both would look like duplicate,
    overlapping visits.

Some older Google Takeout exports use a different, wrapped shape
("semanticSegments": [...], with "placeVisit"/"activitySegment" keys and
numeric lat/lng E7 values). That shape is also supported as a fallback.
"""
from datetime import datetime
from typing import Any, Optional

from dateutil import parser as dateutil_parser


class TimelineParseError(ValueError):
    pass


def _get(d: Any, *keys, default=None):
    """Walk nested dict keys, returning `default` on any miss."""
    cur = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur if cur is not None else default


def _first(*values):
    for v in values:
        if v not in (None, ""):
            return v
    return None


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return dateutil_parser.isoparse(value)
    except (ValueError, TypeError):
        return None


def _parse_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_geo(value: Optional[str]):
    """'geo:-33.960123,18.470456' or '-33.96,18.47' -> (-33.96, 18.47)"""
    if not value or "," not in value:
        return None, None
    value = value.strip()
    if value.startswith("geo:"):
        value = value[4:]
    try:
        lat_str, lng_str = value.split(",", 1)
        return float(lat_str.strip()), float(lng_str.strip())
    except (ValueError, TypeError):
        return None, None


def _parse_visit_segment(segment: dict) -> Optional[dict]:
    # Real exports nest sub-visits inside a broader visit at the same or an
    # overlapping time window ("hierarchyLevel": "1", a different placeID —
    # e.g. a specific shop inside a shopping centre). The Timeline app itself
    # only surfaces the top-level ("0") segment in its daily list, and
    # importing the nested ones too would look like duplicate/overlapping
    # visits, so only hierarchyLevel "0" (or schemas that don't have the
    # field at all, e.g. older Takeout exports) is imported.
    hierarchy_level = _get(segment, "visit", "hierarchyLevel")
    if hierarchy_level is not None and hierarchy_level != "0":
        return None

    start = _parse_time(
        _first(segment.get("startTime"), _get(segment, "placeVisit", "duration", "startTimestamp"))
    )
    end = _parse_time(
        _first(segment.get("endTime"), _get(segment, "placeVisit", "duration", "endTimestamp"))
    )
    if not start or not end:
        return None

    # current on-device export schema
    top = _get(segment, "visit", "topCandidate", default={})
    semantic_type = top.get("semanticType")
    place_id = top.get("placeID")
    name = _first(_get(top, "placeLocation", "name"), top.get("name"))
    address = _get(top, "placeLocation", "address")
    lat, lng = _parse_geo(_first(_get(top, "placeLocation"), top.get("placeLocation")))
    if lat is None:
        # some variants nest coordinates one level deeper: placeLocation.latLng
        lat, lng = _parse_geo(_get(top, "placeLocation", "latLng"))

    # older Takeout schema fallback
    if name is None and address is None and lat is None:
        location = _get(segment, "placeVisit", "location", default={})
        name = location.get("name")
        address = location.get("address")
        place_id = place_id or location.get("placeId")
        lat_e7, lng_e7 = location.get("latitudeE7"), location.get("longitudeE7")
        lat = lat_e7 / 1e7 if isinstance(lat_e7, (int, float)) else None
        lng = lng_e7 / 1e7 if isinstance(lng_e7, (int, float)) else None

    if not name and semantic_type and semantic_type != "Unknown":
        name = semantic_type

    return {
        "entry_type": "visit",
        "location_name": name or "",
        "address": address or "",
        "latitude": lat,
        "longitude": lng,
        "place_id": place_id,
        "start_time": start,
        "end_time": end,
        "raw_data": segment,
    }


def _parse_drive_segment(segment: dict) -> Optional[dict]:
    start = _parse_time(
        _first(segment.get("startTime"), _get(segment, "activitySegment", "duration", "startTimestamp"))
    )
    end = _parse_time(
        _first(segment.get("endTime"), _get(segment, "activitySegment", "duration", "endTimestamp"))
    )
    if not start or not end:
        return None

    distance_m = _parse_float(
        _first(_get(segment, "activity", "distanceMeters"), _get(segment, "activitySegment", "distance"))
    )
    distance_km = round(distance_m / 1000, 2) if distance_m is not None else None

    return {
        "entry_type": "drive",
        "location_name": "Driving",
        "address": "",
        "latitude": None,
        "longitude": None,
        "place_id": None,
        "distance_km": distance_km,
        "start_time": start,
        "end_time": end,
        "raw_data": segment,
    }


def parse_timeline(data) -> list:
    """
    Accepts either the bare array a real on-device export contains, or the
    older {"semanticSegments": [...]} wrapped shape. Returns a list of
    dicts (one per visit/drive; timelinePath breadcrumb segments are
    skipped), each with keys matching TimelineEntry fields, ready for
    `TimelineEntry.objects.create(**entry, source="google")`.
    """
    if isinstance(data, list):
        segments = data
    elif isinstance(data, dict):
        segments = data.get("semanticSegments")
    else:
        segments = None

    if segments is None:
        raise TimelineParseError(
            "Couldn't find timeline segments in this file — expected either "
            "a bare JSON array or an object with a 'semanticSegments' array. "
            "Is this a Timeline.json / location-history.json export?"
        )

    entries = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        if "visit" in segment or "placeVisit" in segment:
            parsed = _parse_visit_segment(segment)
        elif "activity" in segment or "activitySegment" in segment:
            parsed = _parse_drive_segment(segment)
        else:
            parsed = None  # timelinePath or unrecognised segment
        if parsed:
            entries.append(parsed)

    entries.sort(key=lambda e: e["start_time"])
    return entries
