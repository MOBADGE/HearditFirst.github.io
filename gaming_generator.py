
import os
import datetime
import textwrap
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from openai import OpenAI

# ------------- CONFIG -------------

GAMING_FEEDS = [
    "https://www.pcgamer.com/rss/",
    "https://www.gamespot.com/feeds/mashup/",
    "https://www.polygon.com/rss/index.xml",
    "https://www.eurogamer.net/feed/news",
]

MAX_ARTICLES = 10
GAME_KEYWORDS = [
    "game", "games", "gaming", "videogame", "video game",
    "xbox", "playstation", "ps5", "ps4", "nintendo", "switch",
    "steam", "epic games", "valve", "riot", "blizzard",
    "esport", "esports", "tournament", "dlc", "patch", "update",
    "fps", "rpg", "mmo", "mmorpg", "battle royale", "indie game",
]


client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ------------- HELPERS -------------

def fetch_rss_items():
    """Pull items from gaming RSS feeds."""
    items = []

    for feed in GAMING_FEEDS:
        try:
            resp = requests.get(feed, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)

            for item in root.iter("item"):
                title = item.findtext("title", "").strip()
                desc = item.findtext("description", "").strip()
                link = item.findtext("link", "").strip()
                pub_raw = item.findtext("pubDate", "").strip()
                
                if not title:
                    continue
                

            text = (title + " " + desc).lower()
                    
                    items.append({
                        "title": title,
                        "description": desc,
                        "link": link,
                        "pub_raw": pub_raw,
                    })
        except Exception as e:
            print("Error fetching {}: {}".format(feed, e))

    # De-duplicate by title
    seen = set()
    unique = []
    for it in items:
        if it["title"] not in seen:
            seen.add(it["title"])
            unique.append(it)

    return unique[:MAX_ARTICLES]


def format_date(raw):
    """Convert RSS date -> YYYY-MM-DD."""
    if not raw:
        return "Unknown"
    try:
        dt = parsedate_to_datetime(raw)
        return dt.date().strftime("%Y-%m-%d")
    except Exception:
        return raw


def build_prompt(items):
    """Build the prompt for summarizing gaming news."""
    bullets = []
    for i, it in enumerate(items, start=1):
        bullets.append(
            "{}. {}\n   Date: {}\n   {}\n   Link: {}".format(
                i,
                it["title"],
                format_date(it["pub_raw"]),
                it["description"],
                it["link"],
            )
        )

    articles_block = "\n\n".join(bullets)

    prompt = f"""
Summarize today's most important GAMING news into a clear, readable briefing.

Scope (include ONLY stories that clearly fit these):
- Video games (PC, console, mobile)
- Board games and tabletop
- Esports and competitive gaming
- Major business/industry moves that directly affect games or gamers

Ignore:
- General tech, streaming, politics, or entertainment stories unless they directly impact games or gamers.

Requirements:
- 3–6 sections with clear headers.
- Format each section header as a markdown level-3 heading starting with "### ".
- 350–600 words total.
- Plain, neutral tone.
- Explain what happened and why it matters.
- No hype, no buzzwords, no futurism.

Articles:
{articles_block}
"""


    return textwrap.dedent(prompt).strip()


def ask_chatgpt(prompt):
    """Call OpenAI API."""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You write calm, simple, neutral gaming news summaries.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=900,
    )
    return response.choices[0].message.content.strip()




def convert_summary_to_html(summary):
    """Turn ChatGPT's markdown-style output into HTML blocks.

    - Lines starting with '###' become <h2> headings.
    - Lines that are ONLY '**Title**' (markdown bold) also become <h2>.
    - Filter out non-gaming sections based on GAME_KEYWORDS.
    - Everything else becomes a normal <p>.
    """

    GAME_KEYWORDS = [
        "game", "gaming", "xbox", "playstation", "ps5", "nintendo",
        "switch", "steam", "pc release", "dlc", "update", "patch",
        "league of legends", "valorant", "esports", "tournament",
        "blizzard", "activision", "bethesda", "ubisoft", "epic",
    ]

    html = ""

    for block in summary.split("\n\n"):
        text = block.strip()
        if not text:
            continue

        # ---------- FILTER OUT NON-GAMING HEADERS ----------
        lowered = text.lower()
        if (text.startswith("###") or (text.startswith("**") and text.endswith("**"))):
            if not any(k in lowered for k in GAME_KEYWORDS):
                # Skip headings that are clearly not gaming
                continue

        # Case 1: proper markdown header (### Title)
        if text.startswith("###"):
            title = text.lstrip("#").strip()
            html += f"<h2>{title}</h2>\n"
            continue

        # Case 2: bold-only header (**Title**)
        if (
            text.startswith("**")
            and text.endswith("**")
            and text.count("**") == 2
            and len(text) > 4
        ):
            title = text.strip("*").strip()
            html += f"<h2>{title}</h2>\n"
            continue

        # Default: paragraph
        html += f"<p>{text}</p>\n"

    return html

def update_gaming_page(summary_html, today):
    """Replace the <div id='article'>...</div> content inside gaming.html."""
    display_date = today.strftime("%B %d, %Y")

    with open("gaming.html", "r", encoding="utf-8") as f:
        html = f.read()

    marker = '<div id="article">'
    start = html.find(marker)
    if start == -1:
        raise RuntimeError('gaming.html missing <div id="article">')

    start_tag_end = html.find(">", start)
    end = html.find("</div>", start_tag_end)

    before = html[: start_tag_end + 1]
    after = html[end:]

    inner_html = (
        "\n<p class=\"article-date\">Updated: "
        + display_date +
        "</p>\n"
        + summary_html +
        "\n"
    )

    new_html = before + inner_html + after

    with open("gaming.html", "w", encoding="utf-8") as f:
        f.write(new_html)

    print("gaming.html updated with new gaming summary.")


def write_gaming_archive_page(summary_html, today):
    """Write a full standalone archive page for today's gaming digest."""
    archive_dir = "gaming_archives"
    os.makedirs(archive_dir, exist_ok=True)

    date_slug = today.strftime("%Y-%m-%d")
    display_date = today.strftime("%B %d, %Y")
    path = os.path.join(archive_dir, "{}.html".format(date_slug))

    page_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Gaming Digest - {display}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" type="image/png" href="/favicon.png" />
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #020617;
      color: #e5e7eb;
      padding: 1.5rem;
    }}
    .page {{
      max-width: 900px;
      margin: 0 auto;
    }}
    h1 {{
      margin-top: 0;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 1.4rem;
    }}
    .date {{
      color: #9ca3af;
      font-size: 0.9rem;
      margin-bottom: 1rem;
    }}
    h2 {{
      margin-top: 1.6rem;
      margin-bottom: 0.5rem;
      font-size: 1.2rem;
    }}
    p {{
      line-height: 1.7;
      font-size: 0.95rem;
    }}
    a {{
      color: #38bdf8;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .back {{
      margin-top: 1.5rem;
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <div class="page">
    <h1>A Little Birdy - Gaming News</h1>
    <div class="date">{display}</div>
    {body}
    <p class="back"><a href="/gaming.html">&larr; Back to latest gaming digest</a></p>
  </div>
</body>
</html>
""".format(display=display_date, body=summary_html)

    with open(path, "w", encoding="utf-8") as f:
        f.write(page_html)

    print("Wrote gaming archive page {}".format(path))


def build_gaming_archive_list_html():
    """Build the <li> list for the Gaming Archives sidebar."""
    archive_dir = "gaming_archives"

    if not os.path.isdir(archive_dir):
        return '<li class="archive-empty">No previous gaming digests yet.</li>'

    entries = []

    for filename in os.listdir(archive_dir):
        if not filename.endswith(".html"):
            continue
        slug = filename[:-5]  # strip .html

        try:
            dt = datetime.datetime.strptime(slug, "%Y-%m-%d").date()
            display = dt.strftime("%B %d, %Y")
        except ValueError:
            display = slug

        entries.append((slug, display))

    if not entries:
        return '<li class="archive-empty">No previous gaming digests yet.</li>'

    # newest first
    entries.sort(reverse=True, key=lambda x: x[0])

    lines = [
        '<li><a href="gaming_archives/{slug}.html">{display}</a></li>'.format(
            slug=slug, display=display
        )
        for slug, display in entries
    ]

    return "\n".join(lines)


def update_gaming_archive_list_on_page():
    """Update the <ul id="gaming-archive-list"> in gaming.html."""
    with open("gaming.html", "r", encoding="utf-8") as f:
        html = f.read()

    marker = '<ul id="gaming-archive-list">'
    start = html.find(marker)
    if start == -1:
        raise RuntimeError('gaming.html missing <ul id="gaming-archive-list">')

    start_tag_end = html.find(">", start)
    end = html.find("</ul>", start_tag_end)

    before = html[: start_tag_end + 1]
    after = html[end:]

    inner = "\n" + build_gaming_archive_list_html() + "\n"

    new_html = before + inner + after

    with open("gaming.html", "w", encoding="utf-8") as f:
        f.write(new_html)

    print("gaming.html archive list updated.")


# ------------- MAIN -------------

def main():
    items = fetch_rss_items()
    if not items:
        print("No gaming items fetched.")
        return

    today = datetime.date.today()

    prompt = build_prompt(items)
    summary = ask_chatgpt(prompt)
    summary_html = convert_summary_to_html(summary)

    write_gaming_archive_page(summary_html, today)
    update_gaming_page(summary_html, today)
    update_gaming_archive_list_on_page()


if __name__ == "__main__":
    main()
