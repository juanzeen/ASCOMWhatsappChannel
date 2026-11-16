import hmac
import httpx
import os
import dotenv
import asyncio
from typing import Annotated
from fastapi import FastAPI, Header, HTTPException, Depends
from contextlib import asynccontextmanager
from .services.messages import extract_and_send_messages
from .services.db import save_sent_posts
from .dependencies import get_db
from postgrest.exceptions import APIError

dotenv.load_dotenv()

WAHA_URL = os.getenv("WAHA_URL")
CRON_SECRET = os.getenv("CRON_SECRET")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Checking WAHA...")
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(f"{WAHA_URL}/ping",timeout=3.0)
                if response.status_code == 200:
                    print("WAHA is working.")
                    break
            except (httpx.RequestError, httpx.HTTPStatusError):
                pass

            await asyncio.sleep(1)
    yield

app = FastAPI(lifespan=lifespan,docs_url=None, redoc_url=None, openapi_url=None)



def check_secret(authorization: Annotated[str | None, Header()] = None):
    if not CRON_SECRET:
        raise HTTPException(
            status_code=500, detail={"message": "SECRET is not configured."}
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"message": "Missing or malformed Authorization header."},
        )
    token = authorization.split("Bearer ", 1)[1]
    if not hmac.compare_digest(token, CRON_SECRET):
        raise HTTPException(status_code=403, detail={"message": "Invalid token."})


@app.get("/")
async def root(db=Depends(get_db)):
    health_status = {
        "status": "healthy",
        "services": {"api": "healthy", "database": "unknown"},
    }
    try:
        ping = await db.table("posts").select("*").limit(1).execute()
        if ping:
            health_status["services"]["database"] = "healthy"
        return health_status
    except APIError as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = "unhealthy"
        health_status["services"]["error"] = "Unavailable database."
        raise HTTPException(503, detail=health_status)
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = "unhealthy"
        health_status["services"]["api"] = "unhealthy"
        health_status["services"]["error"] = "Internal server error."
        raise HTTPException(500, detail=health_status)

@app.post("/sync")
async def sync(auth=Depends(check_secret)):
    sent = await extract_and_send_messages()

    if len(sent) > 0:
        response = await save_sent_posts(sent)
        data = {"total": len(sent), "sent": sent, "inserted": response}
        return {"data": data, "message": "Messages were successfully sent."}
    return {
        "data": {"total": 0, "sent": [], "inserted": []},
        "message": "No posts have been added.",
    }
