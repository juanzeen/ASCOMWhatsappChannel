from ..dependencies import get_db

FIELDS = [
    "id",
    "title",
    "link"]


async def save_sent_posts(posts: list[dict[str, str| int]]):
    supabase = await get_db()
    filtered = []
    for s in posts:
        filtered_dict = {k: v for k, v in s.items() if k in FIELDS}
        filtered.append(filtered_dict)
    response = await supabase.table("posts").insert(filtered).execute()
    return response.data

async def get_sent_posts():
    db = await get_db()
    db_data = await db.table("posts").select("id").execute()
    saved_posts = set(d["id"] for d in db_data.data)
    return saved_posts
