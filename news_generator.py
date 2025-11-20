import os
import datetime
import textwrap
import requests
import xml.etree.ElementTree as ET

from openai import OpenAI

# --- Config ---
# You can change these later if you want different news sources
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://feeds.reuters.com/reuters/topNews",
    "https://feeds.apnews.com/apf-topnews",
]

# Max number of articles to include in the summary
MAX_ARTICLES = 5

# OpenAI client – reads the key from the environment variable we set as a GitHub secret
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def fetch_rss_items():
    """Fetch top items from the RSS feeds."""
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
                if title:
                    items.append({"title": title, "description": desc, "link": link})
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


def build_prompt(items):
    """Build the prompt we send to ChatGPT from the news items."""
    bullets = []
    for i, it in enumerate(items, start=1):
        bullets.append(
            f"{i}. {it['title']}\n   {it['description']}\n   Link: {it['link']}"
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
    """Replace the article content in index.html with the new summary."""
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


def main():
    items = fetch_rss_items()
    if not items:
        print("No news items fetched. Exiting.")
        return

    prompt = build_prompt(items)
    summary = ask_chatgpt(prompt)

    # Convert paragraphs (split on double newlines) to HTML <p> tags
    paragraphs = "".join(
        f"<p>{block.strip()}</p>\n"
        for block in summary.split("\n\n")
        if block.strip()
    )

    update_index_html(paragraphs)
    print("index.html updated with new daily brief.")


if __name__ == "__main__":
    main()
