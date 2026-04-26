import os
import requests
from typing import List
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")


# ─────────────────────────────────────────
# YOUTUBE
# ─────────────────────────────────────────
def search_youtube(query: str, max_results: int = 10) -> List[dict]:
    if not YOUTUBE_API_KEY:
        print("No YouTube API key found")
        return []

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        items = response.json().get("items", [])

        results = []
        for item in items:
            video_id = item["id"]["videoId"]
            results.append({
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "thumbnail_url": item["snippet"]["thumbnails"]["high"]["url"],
                "platform": "youtube"
            })
        return results

    except Exception as e:
        print(f"YouTube search error: {e}")
        return []


def get_youtube_thumbnail(video_url: str) -> str:
    video_id = video_url.split("v=")[-1].split("&")[0]
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"


# ─────────────────────────────────────────
# SERPAPI — Google Images
# ─────────────────────────────────────────
SKIP_DOMAINS = [
    "lookaside.instagram.com",
    "lookaside.fbsbx.com",
    "facebook.com",
    "img.olympics.com/images/image/private",  # auth-gated
]

def is_skippable_url(url: str) -> bool:
    return any(skip in url for skip in SKIP_DOMAINS)

def search_google_images_serp(query: str, max_results: int = 100) -> List[dict]:
    if not SERP_API_KEY:
        print("No SerpAPI key found")
        return []

    url = "https://serpapi.com/search"
    params = {
        "engine": "google_images",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": max_results,
        "safe": "active"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        items = response.json().get("images_results", [])

        results = []
        for item in items:
            image_url = item.get("original")
            if image_url and not is_skippable_url(image_url):
                results.append({
                    "url": item.get("link", image_url),
                    "image_url": image_url,
                    "title": item.get("title", ""),
                    "platform": "google_images"
                })
        return results

    except Exception as e:
        print(f"SerpAPI Google Images error: {e}")
        return []
    
def search_google_web_serp(query: str, max_results: int = 10) -> List[dict]:
    if not SERP_API_KEY:
        print("No SerpAPI key found")
        return []

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": max_results
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        items = response.json().get("organic_results", [])

        results = []
        for item in items:
            # Try to get thumbnail from search result
            thumbnail = item.get("thumbnail")
            if not thumbnail:
                # Try rich snippet image
                thumbnail = item.get("rich_snippet", {}).get(
                    "top", {}
                ).get("detected_extensions", {}).get("image")

            if thumbnail:
                results.append({
                    "url": item.get("link"),
                    "image_url": thumbnail,
                    "title": item.get("title", ""),
                    "platform": "google_web"
                })
        return results

    except Exception as e:
        print(f"SerpAPI Google Web error: {e}")
        return []


# ─────────────────────────────────────────
# REDDIT (free, no API key needed)
# ─────────────────────────────────────────
def search_reddit(query: str, max_results: int = 10) -> List[dict]:
    url = "https://www.reddit.com/search.json"
    headers = {"User-Agent": "MediaShield/1.0"}
    params = {
        "q": query,
        "type": "link",
        "limit": max_results,
        "sort": "new"
    }

    try:
        response = requests.get(
            url, headers=headers,
            params=params, timeout=10
        )
        response.raise_for_status()
        posts = response.json().get("data", {}).get("children", [])

        results = []
        for post in posts:
            data = post.get("data", {})
            image_url = data.get("url", "")
            if any(image_url.endswith(ext)
                   for ext in [".jpg", ".jpeg", ".png", ".gif"]):
                results.append({
                    "url": f"https://reddit.com{data.get('permalink')}",
                    "image_url": image_url,
                    "title": data.get("title", ""),
                    "platform": "reddit"
                })
        return results

    except Exception as e:
        print(f"Reddit search error: {e}")
        return []


# ─────────────────────────────────────────
# COMBINED SEARCH
# ─────────────────────────────────────────
def search_all_platforms(
    query: str,
    max_per_platform: int = 10
) -> List[dict]:
    all_results = []

    # YouTube
    yt_results = search_youtube(query, max_per_platform)
    for r in yt_results:
        r["image_url"] = get_youtube_thumbnail(r["url"])
        all_results.append(r)

    # Google Images via SerpAPI
    gi_results = search_google_images_serp(query, max_per_platform)
    all_results.extend(gi_results)

    # Google Web via SerpAPI (catches Instagram, blogs, news)
    gw_results = search_google_web_serp(query, max_per_platform)
    all_results.extend(gw_results)

    # Reddit (free)
    rd_results = search_reddit(query, max_per_platform)
    all_results.extend(rd_results)

    print(
        f"Total: {len(all_results)} | "
        f"YouTube: {len(yt_results)} | "
        f"Google Images: {len(gi_results)} | "
        f"Google Web: {len(gw_results)} | "
        f"Reddit: {len(rd_results)}"
    )

    return all_results