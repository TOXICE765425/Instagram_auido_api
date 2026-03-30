from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import re
import json

RAPIDAPI_KEY = "b0a2cb029bmshac2aa1c4943d70ep1db3c3jsnfcc34a9dcfc1"
RAPIDAPI_HOST = "instagram-reels-downloader-api.p.rapidapi.com"


def is_valid_instagram_url(url: str) -> bool:
    pattern = r'https?://(www\.)?instagram\.com/(reel|p|tv)/[\w-]+'
    return bool(re.search(pattern, url))


def get_audio(url):
    if not is_valid_instagram_url(url):
        return 400, {
            "success": False,
            "message": "Invalid Instagram URL. Format: https://www.instagram.com/reel/XXXXX/"
        }

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
            return 404, {
                "success": False,
                "message": "Video URL nahi mila.",
                "raw_response": data
            }

        clean_title = title.replace("on Instagram: ", "").strip('"').strip()

        return 200, {
            "success": True,
            "result": {
                "title": clean_title,
                "video_url": video_url,
                "source_url": url
            }
        }

    except requests.exceptions.Timeout:
        return 504, {"success": False, "message": "Request timeout. Dobara try karo."}
    except requests.exceptions.HTTPError as e:
        return 500, {"success": False, "message": f"API error: {str(e)}"}
    except Exception as e:
        return 500, {"success": False, "message": f"Server error: {str(e)}"}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')

        if parsed.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": "Use /audio?url=instagram_reel_url"
            }).encode())

        elif parsed.path == '/audio':
            url_param = params.get('url', [None])[0]
            if not url_param:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "url parameter do. Example: /audio?url=https://www.instagram.com/reel/XXXXX/"
                }).encode())
            else:
                status, result = get_audio(url_param)
                self.send_response(status)
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": "Route nahi mila. Use /audio?url=..."
            }).encode())
