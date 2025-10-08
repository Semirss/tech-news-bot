import feedparser
import requests
import random
import json
import os
from datetime import date
from flask import Flask
import threading
import time

# Load credentials from environment variables
TOKEN = os.environ.get('TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_KEY')
GROUPS = ['@semirgp1', '@semirgp2', '@semirgp3', '@semirgp4', '@semirgp5', '@semirgp6', '@semirgp7']


# RSS Feeds (100 reliable and diverse feeds)
RSS_FEEDS = [
    # Technology
    'https://www.theverge.com/rss/index.xml',
    'https://www.wired.com/feed/rss',
    'https://feeds.arstechnica.com/arstechnica/index',
    'https://feeds.feedburner.com/TechCrunch/',
    'https://hnrss.org/frontpage',
    'https://nitter.net/TechCrunch/rss',
    'https://medium.com/feed/tag/technology',
    'https://www.techradar.com/rss',
    'https://www.gadgets360.com/rss',
    'https://www.cnet.com/rss/news/',
    'https://www.computerweekly.com/rss',
    'https://www.techxplore.com/rss-feed/',
    'https://www.engadget.com/rss.xml',
    'https://www.technologyreview.com/feed/',
    'https://www.zdnet.com/news/rss.xml',
    'https://www.bbc.com/news/technology/rss.xml',
    'https://www.cbsnews.com/rss/technology/',
    'https://www.reuters.com/rssFeed/technologyNews',
    'https://www.scientificamerican.com/feed/',
    'https://www.sciencedaily.com/rss/computers_math.xml',
    # Science
    'https://www.sciencedaily.com/rss/top/science.xml',
    'https://www.nature.com/subjects/rss',
    'https://www.phys.org/rss-feed/',
    'https://www.sciencedaily.com/rss/top/health.xml',
    'https://www.sciencedaily.com/rss/top/space_time.xml',
    'https://www.sciencedaily.com/rss/top/environment.xml',
    'https://www.sciencenews.org/feed',
    'https://www.scientificamerican.com/feed/',
    # Business / Startups
    'https://www.cnbc.com/id/100003114/device/rss/rss.html',
    'https://www.forbes.com/technology/feed2/',
    'https://www.businessinsider.com/rss',
    'https://techcrunch.com/feed/',
    'https://venturebeat.com/feed/',
    'https://www.economist.com/technology-quarterly/rss.xml',
    # Misc news
    'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/Science.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/Health.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/Education.xml',
    'https://feeds.a.dj.com/rss/RSSWorldNews.xml',
    'https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml',
    'https://feeds.a.dj.com/rss/WSJcomUSTech.xml',
    'https://feeds.a.dj.com/rss/WSJcomUSLife.xml',
    # Gadgets
    'https://www.gsmarena.com/rss-news-reviews.php',
    'https://www.androidpolice.com/feed/',
    'https://www.phonearena.com/rss/news',
    'https://www.androidauthority.com/feed/',
    # Add more reliable sources to reach 100
    'https://www.space.com/feeds/all',
    'https://www.space.com/news',
    'https://www.nationalgeographic.com/feeds/rss',
    'https://www.nationalgeographic.com/science/article.rss',
    'https://www.newscientist.com/feed/home/',
    'https://www.scientificamerican.com/feed/',
    'https://www.popularmechanics.com/rss/all.xml',
    'https://www.popularmechanics.com/space/',
    'https://www.popularmechanics.com/technology/',
    'https://www.popularmechanics.com/science/',
    'https://www.sciencemag.org/rss/news_current.xml',
    'https://www.sciencemag.org/rss/shortcuts.xml',
    'https://www.sciencemag.org/rss/insight.xml',
    'https://www.sciencemag.org/rss/research-highlights.xml',
    'https://www.sciencemag.org/rss/editorials.xml',
    'https://www.sciencemag.org/rss/commentaries.xml',
    'https://www.sciencemag.org/rss/features.xml',
    'https://www.sciencemag.org/rss/news-analysis.xml',
    'https://www.sciencemag.org/rss/news-opinion.xml',
    'https://www.sciencemag.org/rss/news-brief.xml',
    'https://www.sciencemag.org/rss/news-review.xml',
    'https://www.sciencemag.org/rss/research-articles.xml',
    'https://www.sciencemag.org/rss/research-reports.xml',
    'https://www.sciencemag.org/rss/news-highlights.xml',
    'https://www.sciencemag.org/rss/research-highlights.xml',
    'https://www.sciencemag.org/rss/editorial-highlights.xml',
    # (You can continue adding feeds up to 100 or mix from multiple categories)
]

LOG_FILE = "posted_articles.json"

def load_posted_links():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_posted_links(log_data):
    with open(LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=2)

def get_unique_article(posted_log):
    random.shuffle(RSS_FEEDS)
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url, request_headers={'User-Agent': 'Mozilla/5.0'})
            for entry in feed.entries:
                if entry.link not in posted_log.get(str(date.today()), []):
                    return entry
        except Exception as e:
            print(f"⚠️ Failed to fetch feed {feed_url}: {e}")
            continue
    return None

def summarize_article(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a tech news summarizer bot. Summarize clearly and briefly."},
            {"role": "user", "content": text}
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print("❌ Error summarizing:", e)
    return "Summary not available."

def send_to_groups(groups, message, photo_url=None):
    for group in groups:
        try:
            if photo_url:
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                data = {
                    "chat_id": group,
                    "photo": photo_url,
                    "caption": message,
                    "parse_mode": "Markdown"
                }
            else:
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                data = {
                    "chat_id": group,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            res = requests.post(url, data=data, timeout=10)
            print(f"✅ Sent to {group}: {res.status_code}")
        except Exception as e:
            print(f"❌ Failed to send to {group}: {e}")

def run_bot():
    posted_log = load_posted_links()
    today_str = str(date.today())
    if today_str not in posted_log:
        posted_log[today_str] = []

    for group in GROUPS:
        article = get_unique_article(posted_log)
        if article:
            title = article.title
            link = article.link
            full_text = article.get("summary", "") or article.get("description", "") or "No content to summarize."
            summary = summarize_article(full_text[:4000])
            msg = f"💫🌐 *{title}*\n\n📄 {summary}\n🔗 [Read more]({link})"

            image_url = None
            if "media_content" in article:
                image_url = article.media_content[0].get('url', None)
            elif "image" in article:
                image_url = article.image.get('href', None)

            send_to_groups([group], msg, photo_url=image_url)
            posted_log[today_str].append(link)
        else:
            print(f"⚠️ No new articles left for {group}.")

    save_posted_links(posted_log)

# Flask for Render + UptimeRobot
app = Flask(__name__)

@app.route('/')
def trigger_bot():
    threading.Thread(target=run_bot).start()
    return "Bot triggered!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
