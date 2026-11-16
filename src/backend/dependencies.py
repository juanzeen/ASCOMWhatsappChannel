from supabase import AsyncClient, acreate_client
import dotenv
import os

dotenv.load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
DB_SECRET = os.getenv("DATABASE_KEY")

async def get_db() -> AsyncClient:
  return await acreate_client(SUPABASE_URL, DB_SECRET)
