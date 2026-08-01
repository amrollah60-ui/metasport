import requests
from bs4 import BeautifulSoup
import time
import re
from io import BytesIO

BOT_TOKEN = "8965625018:AAFTtQ0ByiOUGnDFmY_SU0_YscScyROchA4"
MY_CHANNEL_ID = "@Metaa_sport"
SOURCE_CHANNEL = "varzesh3"

TELEGRAM_BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
seen_posts = set()

def clean_text(text):
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'ورزش سه|ورزش۳|varzesh3', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[👇👈👉☝️👇🏻👇🏼👇🏽👇🏾👇🏿]', '', text)
    text = re.sub(r'[-–—_]{2,}', '', text)
    
    lines = [line.strip() for line in text.splitlines() if line.strip() and len(line.strip()) > 1]
    return "\n".join(lines)

def send_post_to_channel(text, image_url=None):
    clean_caption = clean_text(text)
    final_text = f"{clean_caption}\n\n🆔 {MY_CHANNEL_ID}"
    
    if image_url:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            img_res = requests.get(image_url, headers=headers, timeout=15)
            
            if img_res.status_code == 200 and len(img_res.content) > 1000:
                url = f"{TELEGRAM_BASE_URL}/sendPhoto"
                files = {'photo': ('photo.jpg', BytesIO(img_res.content), 'image/jpeg')}
                data = {
                    "chat_id": MY_CHANNEL_ID,
                    "caption": final_text[:1024]
                }
                res = requests.post(url, data=data, files=files, timeout=20)
                if res.json().get("ok"):
                    print("🖼️ خبر همراه با تصویر ارسال شد.")
                    return res.json()
        except Exception as e:
            print(f"⚠️ خطا در دریافت عکس: {e}")

    url = f"{TELEGRAM_BASE_URL}/sendMessage"
    payload = {
        "chat_id": MY_CHANNEL_ID,
        "text": final_text[:4096],
        "disable_web_page_preview": True
    }
    res = requests.post(url, data=payload, timeout=15)
    if res.json().get("ok"):
        print("📝 خبر متنی ارسال شد.")
        return res.json()
            
    return {}

def extract_posts_from_html(soup):
    posts_data = []
    message_widgets = soup.find_all('div', class_='tgme_widget_message')
    
    for widget in message_widgets:
        text_div = widget.find('div', class_='tgme_widget_message_text')
        if not text_div:
            continue
            
        text_clean = text_div.get_text(separator="\n", strip=True)
        
        image_url = None
        photo_node = widget.find('a', class_='tgme_widget_message_photo_wrap')
        if photo_node:
            style = photo_node.get('style', '')
            match = re.search(r"url\(['\"]?(https?://[^\s'\"]+)['\"]?\)", style)
            if match:
                image_url = match.group(1)

        posts_data.append({
            'raw_text': text_clean,
            'image_url': image_url
        })
        
    return posts_data

def send_latest_3_posts():
    url = f"https://t.me/s/{SOURCE_CHANNEL}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    print("🌐 در حال استخراج آخرین اخبار و تصاویر...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            posts = extract_posts_from_html(soup)
            
            for p in posts:
                seen_posts.add(p['raw_text'])
                
            for p in posts[-3:]:
                send_post_to_channel(p['raw_text'], p['image_url'])
                time.sleep(3)
    except Exception as e:
        print(f"❌ خطا: {e}")

def check_new_posts():
    url = f"https://t.me/s/{SOURCE_CHANNEL}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            posts = extract_posts_from_html(soup)
            
            for p in posts:
                if p['raw_text'] and p['raw_text'] not in seen_posts:
                    print("💥 خبر جدید پیدا شد!")
                    send_post_to_channel(p['raw_text'], p['image_url'])
                    seen_posts.add(p['raw_text'])
                    time.sleep(3)
    except Exception as e:
        print(f"خطا در بررسی خودکار: {e}")

print("🚀 ربات نهایی MetaSport فعال شد...")
send_latest_3_posts()

while True:
    time.sleep(180)
    check_new_posts()
