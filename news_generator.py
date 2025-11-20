import os
import datetime
import textwrap
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from openai import OpenAI

# --- Config ---
# You can change these later if you want different news sources
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://feeds.reuters.com/reuters/topNews",
    "https://feeds.apnews.com/apf-topnews",
]

# Max number of articles to include in the summary
MAX_ARTICLES = 10

# OpenAI client – reads the key from the environment variable we set as a GitHub secret
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

    # Basic dedupe by title
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
        # Convert to date only
        return dt.date().strftime("%Y-%m-%d")
    except Exception:
        # If parsing fails, just return the raw string
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
                "content": "You write calm, neutral, easy-to-read daily news briefings for regular people.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=900,
    )
    return response.choices[0].message.content.strip()


def update_index_html(article_html: str):
    """Replace the article content in index.html with the new summary + sources."""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    today = datetime.date.today().strftime("%B %d, %Y")

    # We assume index.html has:
    # <p class="article-date">...</p>
    # <div id="article"> ... </div>
    marker_start = '<div id="article">'
    marker_end = "</div>"

    if marker_start not in html:
        raise RuntimeError('index.html does not contain <div id="article">')

    # Split around the article div
    before, rest = html.split(marker_start, 1)
    inside, after = rest.split(marker_end, 1)

    # Build new block with updated date and article
    new_article_block = (
        f'<p class="article-date">Updated: {today}</p>\n'
        f'{marker_start}\n{article_html}\n{marker_end}'
    )

    new_html = before + new_article_block + after

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)


def build_sources_html(items):
    """Build an HTML list of sources with their publication dates."""
    if not items:
        return ""

    lines = []
    for it in items:
        date_str = format_pub_date(it.get("pub_date_raw", ""))
        title = it["title"]
        link = it["link"]
        # Basic HTML-escaped-ish output (these fields are from RSS so should be safe enough here)
        lines.append(
            f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a> '
            f'<span class="source-date">({date_str})</span></li>'
        )

    html = "<h2>Sources &amp; Dates</h2>\n<ul>\n" + "\n".join(lines) + "\n</ul>"
    return html


def main():
    items = fetch_rss_items()
    if not items:
        print("No news items fetched. Exiting.")
        return

    prompt = build_prompt(items)
    summary = ask_chatgpt(prompt)

    # Remove any extra "Updated:" lines the model may have added
    summary = "\n".join(
        line for line in summary.split("\n")
        if not line.strip().startswith("Updated:")
    )

    # Convert the summary into HTML: H2 for markdown headers, P for regular text
    summary_html = ""
    for block in summary.split("\n\n"):
        text = block.strip()
        if not text:
            continue

        # If ChatGPT produced a markdown-style header (### Title)
        if text.startswith("###"):
            clean_title = text.lstrip("#").strip()
            summary_html += f"<h2>{clean_title}</h2>\n"
        else:
            summary_html += f"<p>{text}</p>\n"

    # Build sources block with dates
    sources_html = build_sources_html(items)

    # Combine summary + horizontal rule + sources
    full_html = summary_html + "\n<hr />\n" + sources_html

    update_index_html(full_html)
    print("index.html updated with new daily brief and sources.")



if __name__ == "__main__":
    main()
