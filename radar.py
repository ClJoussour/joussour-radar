import os
import json
import requests

# الإعدادات
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_API_TOKEN = os.environ.get("APIFY_API_TOKEN")
PAGE_URL = "https://www.facebook.com/nyabt.al.madt.lldrasat.al.lya"

DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
MEMORY_FILE = os.path.join(DIR, "last_posts_memory.json")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(ids):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(ids, f)

def fetch_facebook_posts():
    print("جاري سحب المنشورات...")
    url = f"https://api.apify.com/v2/acts/apify~facebook-posts-scraper/run-sync-get-dataset-items?token={APIFY_API_TOKEN}"
    r = requests.post(url, json={"startUrls": [{"url": PAGE_URL}], "resultsLimit": 3}, timeout=120)
    if r.status_code in (200, 201):
        return r.json()
    print(f"خطأ: {r.text}")
    return []

def send_to_telegram(text, image_url, post_url):
    message = f"📢 *منشور جديد من الكلية!*\n\n{text}\n\n🔗 [رابط المنشور الأصلي]({post_url})"
    keyboard = json.dumps({"inline_keyboard": [
        [{"text": "✋ أتطوع للتصوير", "callback_data": f"vol_{hash(post_url) % 99999}"}]
    ]})

    if image_url:
        data = {"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": message, "parse_mode": "Markdown", "reply_markup": keyboard}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", data=data)
    else:
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": keyboard}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=data)

    print("تم الإرسال!" if r.status_code == 200 else f"خطأ: {r.text}")

def main():
    old = load_memory()
    new_ids = []
    posts = fetch_facebook_posts()
    if not posts:
        print("لا توجد بيانات.")
        return

    for post in reversed(posts):
        pid = post.get("postId")
        new_ids.append(pid)
        if pid not in old:
            print(f"منشور جديد! ({pid})")
            img = None
            if post.get("media") and len(post["media"]) > 0:
                img = post["media"][0].get("thumbnail") or post["media"][0].get("url")
            send_to_telegram(post.get("text", ""), img, post.get("url", PAGE_URL))
        else:
            print(f"مكرر. ({pid})")

    save_memory(list(set(old + new_ids))[-20:])

if __name__ == "__main__":
    main()
