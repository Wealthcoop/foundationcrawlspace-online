#!/usr/bin/env python3
"""
Foundation, Crawlspace & Drainage Directory Data Harvester
Queries Google Places via Serper for Greater Sacramento, Placer & El Dorado specialists.
Strictly filters to Northern California addresses/coordinates and records only real facts.
"""

import json
import os
import re
import ssl
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_ENV = BASE_DIR.parent / ".env"
OUTPUT_JSON = BASE_DIR / "contractors_data.json"

TARGET_CITIES = [
    {"city": "Sacramento", "county": "Sacramento County", "state": "CA"},
    {"city": "Folsom", "county": "Sacramento County", "state": "CA"},
    {"city": "Roseville", "county": "Placer County", "state": "CA"},
    {"city": "Rocklin", "county": "Placer County", "state": "CA"},
    {"city": "El Dorado Hills", "county": "El Dorado County", "state": "CA"},
    {"city": "Elk Grove", "county": "Sacramento County", "state": "CA"},
    {"city": "Citrus Heights", "county": "Sacramento County", "state": "CA"},
    {"city": "Rancho Cordova", "county": "Sacramento County", "state": "CA"},
    {"city": "Granite Bay", "county": "Placer County", "state": "CA"},
    {"city": "Lincoln", "county": "Placer County", "state": "CA"},
    {"city": "Auburn", "county": "Placer County", "state": "CA"},
    {"city": "Placerville", "county": "El Dorado County", "state": "CA"},
]

QUERY_TEMPLATES = [
    ("Foundation Repair", "foundation repair contractor {city} California"),
    ("Crawlspace Encapsulation", "crawl space waterproofing vapor barrier {city} California"),
    ("Drainage & French Drains", "french drain yard drainage contractor {city} California"),
]

EXCLUDE_NAME_TERMS = [
    "home depot", "lowe's", "lowes", "ace hardware", "harbor freight",
    "walmart", "target", "costco", "menards", "tractor supply",
    "u-haul", "storage", "apartments", "insurance", "realtor", "realty",
    "ferguson", "supply house", "wholesale", "siteone", "roofing", "asphalt", "paving",
    "epoxy", "coating", "coatings", "siding", "deck builder", "drafting", "pool", "pools"
]

INCLUDE_HINTS = [
    "foundation", "crawl", "waterproof", "drain", "level", "pier", "underpin",
    "concrete", "excavat", "earth", "structur", "moisture", "sump", "vapor",
    "grading", "landscape", "seismic", "retrofit", "basement", "construct",
    "water damage", "restoration"
]

NON_CA_AREA_CODES = {
    "205", "251", "256", "334", "404", "470", "478", "678", "706", "762", "770", "912",
    "239", "305", "321", "352", "386", "407", "561", "727", "754", "772", "786", "813", "850", "863", "904", "941", "954",
    "803", "843", "864", "423", "615", "731", "865", "901", "931",
    "402", "531", "248", "313", "517", "586", "616", "734", "810", "906", "947", "989",
    "612", "651", "763", "952", "206", "253", "360", "425", "509", "503", "541", "971"
}

SSL_CTX = ssl._create_unverified_context()


def load_serper_key() -> str:
    if ROOT_ENV.exists():
        for line in ROOT_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("SERPER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("SERPER_API_KEY", "")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return (phone or "").strip()


def is_in_sac_region(address: str, phone: str, lat, lon) -> bool:
    addr = address or ""
    # Reject explicit non-CA state abbreviations
    other_state = re.search(r",\s*(AL|AK|AZ|AR|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b", addr)
    if other_state:
        return False

    digits = re.sub(r"\D", "", phone or "")
    nat = digits[1:] if len(digits) == 11 and digits.startswith("1") else digits
    area = nat[:3] if len(nat) == 10 else ""
    if area in NON_CA_AREA_CODES:
        return False

    has_ca_addr = bool(re.search(r"(?:,\s*CA\b|\bCA\s+9[456]\d{3}|\bCalifornia\b)", addr, re.I))
    in_sac_bbox = False
    try:
        if lat is not None and lon is not None:
            la = float(lat)
            lo = float(lon)
            in_sac_bbox = (38.0 <= la <= 39.35) and (-122.2 <= lo <= -120.3)
    except (TypeError, ValueError):
        pass

    return has_ca_addr or in_sac_bbox


def infer_city_from_address(address: str, fallback_city: str) -> str:
    addr_lower = (address or "").lower()
    for c in TARGET_CITIES:
        if c["city"].lower() in addr_lower:
            return c["city"]
    return fallback_city


def county_for_city(city: str) -> str:
    for c in TARGET_CITIES:
        if c["city"].lower() == city.lower():
            return c["county"]
    return "Greater Sacramento"


def query_places(query: str, city: str, api_key: str) -> list:
    url = "https://google.serper.dev/places"
    payload = json.dumps({
        "q": query,
        "location": f"{city}, California, United States",
        "gl": "us",
        "hl": "en",
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("places", [])
    except Exception as exc:
        print(f"[!] Serper error for '{query}': {exc}")
        return []


def is_relevant(title: str, category: str) -> bool:
    t_low = title.lower()
    c_low = (category or "").lower()
    if any(bad in t_low or bad in c_low for bad in EXCLUDE_NAME_TERMS):
        return False
    combined = f"{t_low} {c_low}"
    return any(hint in combined for hint in INCLUDE_HINTS)


def infer_specialties(title: str, category: str, matched_tags: set) -> list:
    specs = sorted(matched_tags)
    combined = f"{title} {category}".lower()
    if "foundation" in combined or "pier" in combined or "level" in combined:
        if "Foundation Repair" not in specs:
            specs.append("Foundation Repair")
        specs.append("House Leveling & Piers")
    if "crawl" in combined or "vapor" in combined or "moisture" in combined or "waterproof" in combined:
        if "Crawlspace Encapsulation" not in specs:
            specs.append("Crawlspace Encapsulation")
        specs.append("Vapor Barriers & Sump Pumps")
    if "drain" in combined or "french" in combined or "grading" in combined or "excavat" in combined:
        if "Drainage & French Drains" not in specs:
            specs.append("Drainage & French Drains")
    seen = set()
    out = []
    for s in specs:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def main():
    api_key = load_serper_key()
    if not api_key:
        raise SystemExit("SERPER_API_KEY not found in .env or environment.")

    by_key = {}
    for city_info in TARGET_CITIES:
        city = city_info["city"]
        state = city_info["state"]
        for tag, tmpl in QUERY_TEMPLATES:
            query = tmpl.format(city=city, state=state)
            places = query_places(query, city, api_key)
            kept = 0
            for p in places:
                name = re.sub(r"\s+", " ", (p.get("title") or "").strip())
                category = (p.get("category") or "").strip()
                phone = normalize_phone(p.get("phoneNumber", ""))
                address = (p.get("address") or "").strip()
                lat = p.get("latitude")
                lon = p.get("longitude")

                if not name or not is_relevant(name, category):
                    continue
                if not is_in_sac_region(address, phone, lat, lon):
                    continue

                kept += 1
                resolved_city = infer_city_from_address(address, city)
                digits = re.sub(r"\D", "", phone)
                dedupe_key = f"tel:{digits}" if len(digits) >= 10 else f"name:{re.sub(r'[^a-z0-9]', '', name.lower())}"

                raw_rating = p.get("rating")
                raw_reviews = p.get("ratingCount")
                rating_val = float(raw_rating) if raw_rating is not None else None
                review_val = int(raw_reviews) if raw_reviews is not None else 0
                website = (p.get("website") or "").split("?")[0].strip()

                if dedupe_key in by_key:
                    existing = by_key[dedupe_key]
                    existing["_tags"].add(tag)
                    if not existing["website"] and website:
                        existing["website"] = website
                    if existing["rating"] is None and rating_val is not None:
                        existing["rating"] = rating_val
                    if review_val > existing["reviews"]:
                        existing["reviews"] = review_val
                    continue

                by_key[dedupe_key] = {
                    "name": name,
                    "city": resolved_city,
                    "county": county_for_city(resolved_city),
                    "state": state,
                    "rating": rating_val,
                    "reviews": review_val,
                    "phone": phone,
                    "website": website,
                    "address": address or f"{resolved_city}, CA",
                    "latitude": lat,
                    "longitude": lon,
                    "cid": str(p.get("cid") or ""),
                    "category": category or "Foundation & Drainage Contractor",
                    "_tags": {tag},
                    "claimed": False,
                    "featured": False,
                }
            print(f"[*] {city} | {tag}: {kept}/{len(places)} CA-verified")
            time.sleep(0.2)

    contractors = []
    used_slugs = set()
    sorted_items = sorted(
        by_key.values(),
        key=lambda x: (x["city"], -(x["reviews"] or 0), -(x["rating"] or 0.0), x["name"]),
    )

    for idx, item in enumerate(sorted_items, start=1):
        tags = item.pop("_tags")
        base_slug = slugify(f"{item['name']}-{item['city']}") or f"contractor-{idx}"
        slug = base_slug
        n = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{n}"
            n += 1
        used_slugs.add(slug)

        item["id"] = f"FCD-{idx:03d}"
        item["slug"] = slug
        item["services"] = infer_specialties(item["name"], item["category"], tags)
        contractors.append(item)

    OUTPUT_JSON.write_text(json.dumps(contractors, indent=2), encoding="utf-8")
    cities_covered = sorted({c["city"] for c in contractors})
    print(f"\n[OK] Harvested {len(contractors)} CA-verified contractors across {len(cities_covered)} cities.")
    for c in cities_covered:
        cnt = sum(1 for x in contractors if x["city"] == c)
        print(f"   - {c}: {cnt}")


if __name__ == "__main__":
    main()
