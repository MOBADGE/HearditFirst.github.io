import datetime
import json
import os
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html import unescape
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - dependency may be missing in local checks
    OpenAI = None


CATEGORY_CONFIG = {
    "gaming": {
        "label": "Gaming desk",
        "feeds": [
            "https://www.pcgamer.com/rss/",
            "https://www.gamespot.com/feeds/mashup/",
            "https://www.polygon.com/rss/index.xml",
            "https://www.eurogamer.net/feed/",
        ],
    },
    "world": {
        "label": "World desk",
        "feeds": [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://feeds.reuters.com/reuters/worldNews",
            "https://feeds.apnews.com/rss/apf-worldnews",
        ],
    },
    "tech": {
        "label": "Tech desk",
        "feeds": [
            "https://feeds.arstechnica.com/arstechnica/technology",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            "https://www.theverge.com/rss/index.xml",
            "https://www.wired.com/feed/rss",
        ],
    },
    "health": {
        "label": "Health desk",
        "feeds": [
            "https://feeds.bbci.co.uk/news/health/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
            "https://www.statnews.com/feed/",
        ],
    },
}

UTC = datetime.timezone.utc
MAX_ITEMS_PER_CATEGORY = 6
REQUEST_TIMEOUT = 12
CACHE_CONTROL = "s-maxage=900, stale-while-revalidate=3600"

BIASED_PATTERNS = [
    (r"\bbrutal\b", "significant"),
    (r"\bchaotic\b", "disruptive"),
    (r"\bdevastating\b", "serious"),
    (r"\bdevastated\b", "affected"),
    (r"\bdevastate(?:s|d)?\b", "damage"),
    (r"\bviolent\b", "severe"),
    (r"\balarming\b", "notable"),
    (r"\bpunishing\b", "sustained"),
    (r"\bbreakthrough\b", "development"),
    (r"\btransform\b", "change"),
    (r"\bsurge\b", "increase"),
    (r"\bcrack down\b", "increase oversight"),
    (r"\bracing\b", "preparing"),
    (r"\bmounting fears\b", "growing concern"),
    (r"\bhigh-stakes\b", "ongoing"),
    (r"\bteeter(?:ing)?\b", "continue"),
    (r"\bbattle over\b", "discuss"),
    (r"\bcelebrate\b", "report"),
    (r"\bslams?\b", "criticizes"),
    (r"\bfury\b", "reaction"),
    (r"\bpanic\b", "concern"),
    (r"\bshock(?:ing|ed)?\b", "unexpected"),
    (r"\bdramatic\b", "significant"),
    (r"\bexplosive\b", "rapid"),
]

session = requests.Session()
session.headers.update({"User-Agent": "A-Little-Birdy-Told-Me/1.0"})

_openai_client = None


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(UTC)


def get_local_now() -> datetime.datetime:
    try:
        offset_hours = int(os.environ.get("LOCAL_UTC_OFFSET_HOURS", "-6"))
    except Exception:
        offset_hours = -6
    return utc_now() + datetime.timedelta(hours=offset_hours)


def strip_html(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_encoded_content(item: ET.Element) -> str:
    for child in item:
        tag = child.tag or ""
        if tag.lower().endswith("encoded"):
            return (child.text or "").strip()
    return ""


def parse_pub_date(raw: str) -> datetime.datetime | None:
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except Exception:
        return None


def sanitize_text(text: str) -> str:
    current = strip_html(text)
    for pattern, replacement in BIASED_PATTERNS:
        current = re.sub(pattern, replacement, current, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", current).strip()


def compact_text(text: str, limit: int = 240) -> str:
    value = strip_html(text)
    if len(value) <= limit:
        return value
    shortened = value[: limit - 1].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."


def clean_truncation(text: str) -> str:
    if not text:
        return text
    text = text.strip()
    text = re.sub(r"\[\s*\.\s*\.\s*\.\s*\]", "…", text)
    text = re.sub(r"\s*\[\s*\.\s*\.\s*\.\s*\]\s*$", "", text)
    text = re.sub(r"\.{3,}\s*$", "", text)
    text = re.sub(r"…\s*$", "", text)
    return text.strip()


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        key = item["title"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def pick_recent(items: list[dict[str, Any]], max_items: int = MAX_ITEMS_PER_CATEGORY) -> list[dict[str, Any]]:
    local_today = get_local_now().date()
    cutoff = local_today - datetime.timedelta(days=1)
    dated = [item for item in items if item["published_at"] and item["published_at"].date() >= cutoff]
    pool = dated or items
    pool.sort(key=lambda item: item["published_at"] or datetime.datetime.min.replace(tzinfo=UTC), reverse=True)
    return pool[:max_items]


def infer_source_name(url: str) -> str:
    host = urlparse(url).netloc.lower()
    host = host.replace("www.", "")
    if "bbc" in host:
        return "BBC"
    if "reuters" in host:
        return "Reuters"
    if "apnews" in host:
        return "AP"
    if "nytimes" in host:
        return "The New York Times"
    if "arstechnica" in host:
        return "Ars Technica"
    if "theverge" in host:
        return "The Verge"
    if "wired" in host:
        return "Wired"
    if "statnews" in host:
        return "STAT"
    if "pcgamer" in host:
        return "PC Gamer"
    if "gamespot" in host:
        return "GameSpot"
    if "polygon" in host:
        return "Polygon"
    if "eurogamer" in host:
        return "Eurogamer"
    return host or "Source"


def compute_urgency(published_at: datetime.datetime | None, now: datetime.datetime) -> str:
    if not published_at:
        return "Latest"
    age = now - published_at
    hours = age.total_seconds() / 3600
    if hours <= 2:
        return "Breaking"
    if hours <= 8:
        return "Developing"
    if hours <= 24:
        return "Ongoing"
    return "Latest"


def format_relative_time(published_at: datetime.datetime | None, now: datetime.datetime) -> str:
    if not published_at:
        return "Recently"
    delta = now - published_at
    minutes = max(1, int(delta.total_seconds() // 60))
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr ago" if hours == 1 else f"{hours} hrs ago"
    days = hours // 24
    return f"{days} day ago" if days == 1 else f"{days} days ago"


def get_openai_client():
    global _openai_client
    if _openai_client is not None:
        return _openai_client

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None

    _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def infer_tags(category: str, title: str, description: str) -> list[str]:
    haystack = f"{title} {description}".lower()
    tag_map = {
        "tech": [
            ("ai", "AI"),
            ("chip", "Semiconductors"),
            ("cloud", "Cloud"),
            ("security", "Cybersecurity"),
            ("antitrust", "Competition"),
            ("device", "Devices"),
        ],
        "world": [
            ("election", "Politics"),
            ("port", "Logistics"),
            ("ceasefire", "Conflict"),
            ("storm", "Weather"),
            ("power", "Energy"),
            ("trade", "Trade"),
        ],
        "health": [
            ("vaccine", "Vaccines"),
            ("hospital", "Hospitals"),
            ("trial", "Clinical trials"),
            ("virus", "Public health"),
            ("drug", "Treatment"),
            ("cdc", "Guidance"),
        ],
        "gaming": [
            ("steam", "Steam"),
            ("playstation", "PlayStation"),
            ("xbox", "Xbox"),
            ("nintendo", "Nintendo"),
            ("blizzard", "Blizzard"),
            ("patent", "Game industry"),
        ],
    }
    tags = [label for keyword, label in tag_map.get(category, []) if keyword in haystack]
    if not tags:
        tags = [CATEGORY_CONFIG[category]["label"].replace(" desk", "")]
    return tags[:3]


def fetch_feed_items(feed_url: str) -> list[dict[str, Any]]:
    response = session.get(feed_url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items: list[dict[str, Any]] = []

    for item in root.iter("item"):
        title = strip_html(item.findtext("title", ""))
        description = clean_truncation(
            strip_html(get_encoded_content(item) or item.findtext("description", ""))
        )
        link = item.findtext("link", "").strip()
        published_raw = item.findtext("pubDate", "").strip()

        if not title or not link:
            continue

        items.append(
            {
                "title": title,
                "description": description,
                "link": link,
                "published_at": parse_pub_date(published_raw),
            }
        )
    return items


def fetch_category_items(category: str) -> list[dict[str, Any]]:
    gathered: list[dict[str, Any]] = []
    for feed in CATEGORY_CONFIG[category]["feeds"]:
        try:
            gathered.extend(fetch_feed_items(feed))
        except Exception as exc:
            print(f"feed_error {category} {feed}: {exc}")
    return pick_recent(dedupe_items(gathered))


def ai_overview(category: str, items: list[dict[str, Any]]) -> str | None:
    client = get_openai_client()
    if client is None or not items:
        return None

    bullets = []
    for index, item in enumerate(items[:5], start=1):
        bullets.append(
            f"{index}. {item['title']}\n"
            f"   Summary: {item['description']}\n"
            f"   Source: {infer_source_name(item['link'])}"
        )
    prompt = (
        f"Write a two-sentence overview for the {category} desk.\n"
        "Keep it calm, factual, and easy to scan.\n"
        "Do not use hype or dramatic language.\n"
        "Base it only on the bullets below.\n\n"
        + "\n\n".join(bullets)
    )

    try:
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": "You write neutral, concise breaking-news overviews."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=180,
        )
        return strip_html(response.choices[0].message.content or "")
    except Exception as exc:
        print(f"ai_overview_error {category}: {exc}")
        return None


def fallback_overview(category: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return f"The {category} desk is waiting for fresh items."
    lead = sanitize_text(items[0]["description"] or items[0]["title"])
    follow = sanitize_text(items[1]["description"] if len(items) > 1 else items[0]["title"])
    return compact_text(f"Current {category} coverage centers on {lead} Next in view: {follow}", 220)


def build_story(category: str, item: dict[str, Any], now: datetime.datetime) -> dict[str, Any]:
    source_line = compact_text(item["description"] or item["title"], 220)
    clean_line = compact_text(sanitize_text(source_line), 220)
    facts = compact_text(sanitize_text(f"{item['title']}. {item['description']}"), 280)
    return {
        "title": compact_text(item["title"], 140),
        "sourceLine": source_line,
        "cleanLine": clean_line,
        "facts": facts,
        "urgency": compute_urgency(item["published_at"], now),
        "updated": format_relative_time(item["published_at"], now),
        "tags": infer_tags(category, item["title"], item["description"]),
        "link": item["link"],
        "source": infer_source_name(item["link"]),
        "publishedAt": item["published_at"].isoformat() if item["published_at"] else None,
    }


def build_payload(category_filter: str) -> dict[str, Any]:
    now = utc_now()
    categories = [category_filter] if category_filter in CATEGORY_CONFIG else list(CATEGORY_CONFIG.keys())
    response_categories: dict[str, Any] = {}

    for category in categories:
        items = fetch_category_items(category)
        response_categories[category] = {
            "label": CATEGORY_CONFIG[category]["label"],
            "overview": ai_overview(category, items) or fallback_overview(category, items),
            "items": [build_story(category, item, now) for item in items],
        }

    return {
        "site": {
            "name": "A Little Birdy Told Me",
            "domain": "alittlebirdy.org",
        },
        "generatedAt": now.isoformat(),
        "categories": response_categories,
    }


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", CACHE_CONTROL)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json(200, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        try:
            query = parse_qs(urlparse(self.path).query)
            category = query.get("category", ["all"])[0].strip().lower()
            if category not in CATEGORY_CONFIG and category != "all":
                self._send_json(400, {"error": "Invalid category. Use tech, world, health, or all."})
                return
            self._send_json(200, build_payload(category))
        except Exception as exc:
            self._send_json(500, {"error": "Unable to build briefs right now.", "detail": str(exc)})
