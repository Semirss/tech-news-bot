import feedparser
import requests
import random
import json
import os
from datetime import date
from flask import Flask
import threading

# Load credentials from environment variables
TOKEN = os.environ.get('TOKEN')
OPENROUTER_KEY = os.environ.get('OPENROUTER_KEY')

GROUPS = os.environ.get('GROUPS', '@semirgp1,@semirgp2').split(',')  # default if env not set

# RSS Feeds
RSS_FEEDS = [
    'https://www.theverge.com/rss/index.xml',
    'https://www.wired.com/feed/rss',
    'https://feeds.arstechnica.com/arstechnica/index',
    'https://feeds.feedburner.com/TechCrunch/',
    'https://hnrss.org/frontpage',
    'https://nitter.net/TechCrunch/rss',  # Twitter via Nitter
    'https://medium.com/feed/tag/technology'
]

# Store already-posted links
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
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if entry.link not in posted_log.get(str(date.today()), []):
                return entry
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

            summary = summarize_article(full_text[:4000])  # safe for token limit

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

# Flask setup for Render + UptimeRobot
app = Flask(__name__)

@app.route('/')
def trigger_bot():
    threading.Thread(target=run_bot).start()
    return "Bot triggered!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
