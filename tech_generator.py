import os
import datetime
import textwrap
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from openai import OpenAI

# ------------- CONFIG -------------

TECH_FEEDS = [
    "https://feeds.arstechnica.com/arstechnica/technology",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
]

MAX_ARTICLES = 10

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ------------- HELPERS -------------

def fetch_rss_items():
    """Pull items from tech RSS feeds."""
    items = []

    for feed in TECH_FEEDS:
        try:
            resp = requests.get(feed, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)

            for item in root.iter("item"):
                title = item.findtext("title", "").strip()
                desc = item.findtext("description", "").strip()
                link = item.findtext("link", "").strip()
                pub_raw = item.findtext("pubDate", "").strip()

                if title:
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
    """Make a prompt specifically for summarizing tech news."""
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

    prompt = """
    Summarize today's most important TECHNOLOGY news into a clean, readable briefing.

    Requirements:
    - 3-6 sections with clear headers
    - 350-600 words
    - Plain, neutral tone
    - Explain what happened and why it matters
    - No hype, no buzzwords, no futurism

    Articles:
    {articles}
    """.format(articles=articles_block)

    return textwrap.dedent(prompt).strip()


def ask_chatgpt(prompt):
    """Call OpenAI API."""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You write calm, simple, neutral technology news summaries.",
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
    """Turn ChatGPT's markdown-like format into HTML blocks."""
    html = ""

    for block in summary.split("\n\n"):
        text = block.strip()
        if not text:
            continue

        if text.startswith("###"):
            title = text.lstrip("#").strip()
            html += "<h2>{}</h2>\n".format(title)
        else:
            html += "<p>{}</p>\n".format(text)

    return html


def update_tech_page(summary_html):
    """Replace the <div id='article'>...</div> content inside tech.html."""
    today = datetime.datetime.now().strftime("%B %d, %Y")

    with open("tech.html", "r", encoding="utf-8") as f:
        html = f.read()

    marker = '<div id="article">'
    start = html.find(marker)
    if start == -1:
        raise RuntimeError("tech.html missing <div id=\"article\">")

    start_tag_end = html.find(">", start)
    end = html.find("</div>", start_tag_end)

    before = html[: start_tag_end + 1]
    after = html[end:]

    inner_html = (
        "\n<p class=\"article-date\">Updated: "
        + today +
        "</p>\n"
        + summary_html +
        "\n"
    )

    new_html = before + inner_html + after

    with open("tech.html", "w", encoding="utf-8") as f:
        f.write(new_html)

    print("tech.html updated with new tech summary.")


# ------------- MAIN -------------

def main():
    items = fetch_rss_items()
    if not items:
        print("No tech items fetched.")
        return

    prompt = build_prompt(items)
    summary = ask_chatgpt(prompt)
    summary_html = convert_summary_to_html(summary)
    update_tech_page(summary_html)


if __name__ == "__main__":
    main()
