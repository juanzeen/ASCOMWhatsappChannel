import httpx
import feedparser
from bs4 import BeautifulSoup
import asyncio
import os
import dotenv
from .db import get_sent_posts, save_sent_posts

dotenv.load_dotenv()

#Variáveis de ambiente e dicts

WAHA_URL = os.getenv('WAHA_URL')
API_KEY = os.getenv('WAHA_API_KEY')
CHAT_ID = os.getenv('CHAT_ID')
SESSION = os.getenv('SESSION')

EDITAIS = os.getenv('DEFAULT_IMAGE_EDITAIS')
NOTICIAS = os.getenv('DEFAULT_IMAGE_NOTICIAS')

DEFAULT_IMAGES = {
    "Editais": EDITAIS,
    "Notícias": NOTICIAS,
    }

#Utilitários

def clean_summary(text: str):
    sanitized = " ".join(text.split())
    if len(sanitized) > 120:
        return f"{sanitized[:120]}..."
    return sanitized


def format_text_message(post_data: dict[str, str]):
    return f"*{post_data.get('title')}*\n\n{post_data.get('summary')}\n\n📍*Matéria completa:* {post_data.get('link')}"

def extract_id(post_data):
    return post_data.get("id").split("?p=")[1]

def extract_image_src(img_tag: str | None):
    if img_tag:
        return img_tag.get("src")
    return None


async def send_image(message: str, image_url: str):
    payload = {
        "chatId": CHAT_ID,
        "file": {
            "mimetype": "image/jpeg",
            "url": image_url,
            "filename": "image.jpg",
        },
        "caption": format_text_message(message),
        "session": SESSION
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Api-Key": API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(f"{WAHA_URL}/api/sendImage", json=payload, headers=headers)
        if res.is_error:
            error = res.text
            print(f"[RSS BOT][ERROR] Waha error: {error}")
            return False
        return True
    except httpx.RequestError as e:
        print(f"[RSS BOT][ERROR]Connection fail with WAHA: {e}, status: 503")
        return False

async def extract_and_send_messages() -> list[dict[str, str | int]]:
    feed = feedparser.parse("https://uenf.br/portal/feed/")
    saved_posts = await get_sent_posts()
    new_posts = reversed(feed.entries)
    posts = [p for p in new_posts if int(extract_id(p)) not in saved_posts]
    successfully_sent = []

    for p in posts:
        was_sent = False
        summary = clean_summary(
            BeautifulSoup(p.get("summary"), "html.parser").get_text()
        )
        img = extract_image_src(
            BeautifulSoup(p.get("content")[0].get("value"), "html.parser").find("img")
        )
        id = extract_id(p)
        np = {
            "id": id,
            "title": p.get("title"),
            "link": p.get("link"),
            "published": p.get("published"),
            "tag": p.get("tags")[0].get("term"),
            "summary": summary,
        }
        if img is not None:
            was_sent = await send_image(np, img)
        else:
            tag = p.tags[0].get("term")
            default_img = DEFAULT_IMAGES.get(tag)
            was_sent = await send_image(np, default_img)
        if was_sent == True:
            successfully_sent.append(np)
        await asyncio.sleep(1)
    if(len(successfully_sent) > 0):
        inserted_posts = await save_sent_posts(successfully_sent)
        print(f"[RSS BOT][SUCCESS] Total posts sent: {len(successfully_sent)} | Total posts inserted into DB {len(inserted_posts)}")
        for sp in successfully_sent:
            print(f"[RSS BOT][SUCCESS] Title: {sp.get('title')} | ID: {sp.get('id')} | Link: {sp.get('link')}")
        print(f"[RSS BOT][INFO] Database response: {inserted_posts}")
        return successfully_sent
    else:
        print("[RSS BOT][INFO] No posts were sent.")
