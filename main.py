from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import re
from mangum import Mangum

app = FastAPI(title="Instagram Audio Downloader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_KEY = "b0a2cb029bmshac2aa1c4943d70ep1db3c3jsnfcc34a9dcfc1"
RAPIDAPI_HOST = "instagram-reels-downloader-api.p.rapidapi.com"


def is_valid_instagram_url(url: str) -> bool:
    pattern = r'https?://(www\.)?instagram\.com/(reel|p|tv)/[\w-]+'
    return bool(re.search(pattern, url))


@app.get("/")
async def root():
    return JSONResponse(content={
        "success": False,
        "message": "Use /audio?url=instagram_reel_url"
    })


@app.get("/audio")
async def get_audio(url: str = Query(..., description="Instagram Reel URL")):
    if not is_valid_instagram_url(url):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Invalid Instagram URL. Format: https://www.instagram.com/reel/XXXXX/"
            }
        )

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    try:
        response = requests.get(
            f"https://{RAPIDAPI_HOST}/download",
            headers=headers,
            params={"url": url},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        video_url = data.get("videoUrl") or data.get("video_url") or data.get("url")
        title = data.get("title", "")

        if not video_url:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "Video URL nahi mila.",
                    "raw_response": data
                }
            )

        clean_title = title.replace("on Instagram: ", "").strip('"').strip()

        return JSONResponse(content={
            "success": True,
            "result": {
                "title": clean_title,
                "video_url": video_url,
                "source_url": url
            }
        })

    except requests.exceptions.Timeout:
        return JSONResponse(
            status_code=504,
            content={"success": False, "message": "Request timeout. Dobara try karo."}
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "API key invalid ya limit khatam."}
            )
        return JSONResponse(
            status_code=e.response.status_code,
            content={"success": False, "message": f"API error: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

# Vercel ke liye zaroori
handler = Mangum(app)
