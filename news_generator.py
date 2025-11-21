import os
import datetime
import textwrap
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
import re

from openai import OpenAI

# --- Config ---
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://feeds.reuters.com/reuters/topNews",
    "https://feeds.apnews.com/apf-topnews",
]

MAX_ARTICLES = 10

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def fetch_rss_items():
    """Fetch top items from the RSS feeds, including publication dates."""
    items = []
    for feed_url in RSS_FEEDS:
        try:
            resp = requests.get(feed_url, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for item in root.iter("item"):
                title = item.findtext("title", default="").strip()
                desc = item.findtext("description", default="").strip()
                link = item.findtext("link", default="").strip()
                pub_date_raw = item.findtext("pubDate", default="").strip()

                if title:
                    items.append(
                        {
                            "title": title,
                            "description": desc,
                            "link": link,
                            "pub_date_raw": pub_date_raw,
                        }
                    )
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")

    seen = set()
    unique = []
    for it in items:
        if it["title"] not in seen:
            seen.add(it["title"])
            unique.append(it)

    return unique[:MAX_ARTICLES]


def format_pub_date(raw: str) -> str:
    """Convert RSS pubDate string to YYYY-MM-DD where possible."""
    if not raw:
        return "Unknown date"
    try:
        dt = parsedate_to_datetime(raw)
        return dt.date().strftime("%Y-%m-%d")
    except Exception:
        return raw


def build_prompt(items):
    """Build the prompt we send to ChatGPT from the news items."""
    bullets = []
    for i, it in enumerate(items, start=1):
        date_str = format_pub_date(it.get("pub_date_raw", ""))
        bullets.append(
            f"{i}. {it['title']}\n"
            f"   Date: {date_str}\n"
            f"   {it['description']}\n"
            f"   Link: {it['link']}"
        )
    news_block = "\n\n".join(bullets)

    prompt = f"""
    You are an assistant writing a daily news briefing for a general audience.

    Using ONLY the information in the articles below, write a clear, neutral summary of today's most important news. Do not add facts that aren't mentioned.

    Requirements:
    - 3–6 short sections with headers (e.g., "Global Politics", "Economy", "Technology").
    - Plain language, easy to skim.
    - 400–600 words.
    - No sensationalism; focus on what happened, why it matters, and what might come next.

    Here are the articles:

    {news_block}
    """
    return textwrap.dedent(prompt).strip()


def ask_chatgpt(prompt: str) -> str:
    """Send the prompt to ChatGPT (OpenAI API) and return the summary text."""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
 {
    "role": "system",
    "content": (
        "You write calm, neutral, easy-to-read daily news briefings for regular people. "
        "Do NOT guess or infer political titles or offices for any person. "
        "Only describe people using the roles or titles explicitly given in the article text. "
        "If the article does not clearly state that someone is the current or former holder of a role, "
        "just use their name without a title. Never call anyone 'current president' or 'former president' "
        "unless those exact words appear in the article excerpt."
    ),
},

            {"role": "user", "content": prompt},
        ],
        max_tokens=900,
    )
    return response.choices[0].message.content.strip()


def build_sources_html(items):
    """Build an HTML list of sources with their publication dates."""
    if not items:
        return ""

    lines = []
    for it in items:
        date_str = format_pub_date(it.get("pub_date_raw", ""))
        title = it["title"]
        link = it["link"]
        lines.append(
            f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a> '
            f'<span class="source-date">({date_str})</span></li>'
        )

    html = '<h2 class="sources-title">Sources &amp; Dates</h2>\n<ul>\n' + "\n".join(lines) + "\n</ul>"

    return html
    

def sanitize_political_titles(text: str) -> str:
    """
    Neutralize specific political titles that may be outdated or incorrect.
    This keeps your overall style and structure intact.
    """
    patterns = [
        r"\bformer [Pp]resident Donald Trump\b",
        r"\bcurrent [Pp]resident Donald Trump\b",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "Donald Trump", text)
    return text



def update_index_html(article_html: str):
    """
    Replace the content inside the <div id="article">...</div> block.
    If no such div exists, create one before </body>.
    """
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Store the update moment as a UTC timestamp; browser converts to local date
    updated_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    marker_id = 'id="article"'
    pos_id = html.find(marker_id)

    if pos_id != -1:
        # Found existing <div id="article">
        start = html.rfind("<div", 0, pos_id)
        if start == -1:
            raise RuntimeError("Could not find opening <div> for id=\"article\"")

        start_tag_end = html.find(">", start)
        if start_tag_end == -1:
            raise RuntimeError("Could not find end of <div ...> tag for id=\"article\"")

        end = html.find("</div>", start_tag_end)
        if end == -1:
            raise RuntimeError("Could not find closing </div> for <div id=\"article\">")

        before = html[: start_tag_end + 1]
        after = html[end:]

        inner_html = (
            '\n<p class="article-date">Updated: '
            f'<span id="updated-date" data-ts="{updated_ts}"></span>'
            '</p>\n'
            f'{article_html}\n'
        )

        new_html = before + inner_html + after

    else:
        # Fallback: no <div id="article"> found
        print('Warning: id="article" not found; injecting a new article block.')

        article_block = (
            '\n<div id="article">\n'
            '  <p class="article-date">Updated: '
            f'<span id="updated-date" data-ts="{updated_ts}"></span>'
            '</p>\n'
            f'  {article_html}\n'
            '</div>\n'
        )

        body_close = html.lower().rfind("</body>")
        if body_close != -1:
            new_html = html[:body_close] + article_block + html[body_close:]
        else:
            new_html = html + article_block

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)


def write_archive_page(article_html: str, today: datetime.date):
    """Write/overwrite a daily archive page under archives/YYYY-MM-DD.html."""
    date_slug = today.strftime("%Y-%m-%d")
    display_date = today.strftime("%B %d, %Y")

    archive_dir = "archives"
    os.makedirs(archive_dir, exist_ok=True)

    path = os.path.join(archive_dir, f"{date_slug}.html")

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Heard It First – {display_date} Digest</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
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
      max-width: 800px;
      margin: 0 auto;
    }}
    h1 {{
      margin-top: 0;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 1.4rem;
    }}
    .date {{
      margin-bottom: 1rem;
      color: #9ca3af;
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    h2 {{
      font-size: 1.1rem;
      margin: 1.3rem 0 0.4rem;
    }}
    p {{
      line-height: 1.7;
      font-size: 0.95rem;
    }}
    ul {{
      padding-left: 1.2rem;
    }}
    li {{
      margin-bottom: 0.4rem;
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
    <h1>Heard It First – Daily Digest</h1>
    <div class="date">{display_date}</div>
    {article_html}
    <p class="back"><a href="../index.html">← Back to latest digest</a></p>
  </div>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page_html)


def build_archive_list_items():
    """Scan archives/ and build <li> links sorted by date desc."""
    archive_dir = "archives"
    if not os.path.isdir(archive_dir):
        return []

    entries = []
    for name in os.listdir(archive_dir):
        if not name.endswith(".html"):
            continue
        slug = name[:-5]  # strip ".html"
        try:
            dt = datetime.datetime.strptime(slug, "%Y-%m-%d").date()
        except ValueError:
            continue
        display = dt.strftime("%B %d, %Y")
        url = f"archives/{name}"
        entries.append((dt, display, url))

    entries.sort(reverse=True)
    items = [
        f'<li><a href="{url}">{display}</a></li>'
        for dt, display, url in entries
    ]
    return items


def update_archive_list_on_index():
    """Update the <ul id="archive-list">...</ul> block in index.html."""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    marker_id = 'id="archive-list"'
    pos_id = html.find(marker_id)
    if pos_id == -1:
        print('No archive-list element found; skipping archive list update.')
        return

    start = html.rfind("<ul", 0, pos_id)
    if start == -1:
        print("Could not find <ul> for archive-list; skipping.")
        return

    start_tag_end = html.find(">", start)
    if start_tag_end == -1:
        print("Could not find end of <ul> tag for archive-list; skipping.")
        return

    end = html.find("</ul>", start_tag_end)
    if end == -1:
        print("Could not find closing </ul> for archive-list; skipping.")
        return

    before = html[: start_tag_end + 1]
    after = html[end:]

    items = build_archive_list_items()

    if not items:
        inner = '\n<li class="archive-empty">No archives yet.</li>\n'
    else:
        inner = "\n" + "\n".join(items) + "\n"

    new_html = before + inner + after

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)


def main():
    today = datetime.date.today()

    items = fetch_rss_items()
    if not items:
        print("No news items fetched. Exiting.")
        fallback_html = "<p>We couldn't fetch any news right now. Please check back later.</p>"
        update_index_html(fallback_html)
        update_archive_list_on_index()
        return

    prompt = build_prompt(items)
    summary = ask_chatgpt(prompt)

    summary = "\n".join(
        line for line in summary.split("\n")
        if not line.strip().startswith("Updated:")
    )

    summary_html = ""
    for block in summary.split("\n\n"):
        text = block.strip()
        if not text:
            continue

        if text.startswith("###"):
            clean_title = text.lstrip("#").strip()
            summary_html += f"<h2>{clean_title}</h2>\n"
        else:
            summary_html += f"<p>{text}</p>\n"

    sources_html = build_sources_html(items)
    full_html = summary_html + "\n<hr />\n" + sources_html

    # 1) Write today's archive page
    write_archive_page(full_html, today)

    # 2) Update the main index article
    update_index_html(full_html)

    # 3) Refresh the archive list sidebar
    update_archive_list_on_index()

    print("index.html and archives updated with new daily brief and sources.")


if __name__ == "__main__":
    main()
