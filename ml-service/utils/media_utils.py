import requests
import tempfile
import os
from urllib.parse import urlparse

BLOCKED_DOMAINS = [
    "lookaside.instagram.com",
    "lookaside.fbsbx.com",
    "img.olympics.com/images/image/private",
]

def is_blocked_domain(url: str) -> bool:
    try:
        domain = urlparse(url).netloc
        return any(blocked in domain for blocked in BLOCKED_DOMAINS)
    except:
        return True

def is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url

def is_instagram_url(url: str) -> bool:
    return "instagram.com" in url and url.startswith("http")

def get_youtube_thumbnail_direct(url: str) -> str:
    """
    Gets YouTube thumbnail using YouTube Data API (official, always works)
    """
    if "v=" in url:
        video_id = url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
    else:
        raise ValueError(f"Cannot extract YouTube video ID from: {url}")

    youtube_api_key = os.getenv("YOUTUBE_API_KEY")

    # Use YouTube Data API to get video details + thumbnail
    if youtube_api_key:
        try:
            api_url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet",
                "id": video_id,
                "key": youtube_api_key
            }
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            items = response.json().get("items", [])

            if items:
                thumbnails = items[0]["snippet"]["thumbnails"]
                # Get highest quality available
                for quality in ["maxres", "standard", "high", "medium", "default"]:
                    if quality in thumbnails:
                        thumb_url = thumbnails[quality]["url"]
                        img_response = requests.get(thumb_url, timeout=15)
                        if img_response.status_code == 200:
                            tmp = tempfile.NamedTemporaryFile(
                                delete=False, suffix=".jpg"
                            )
                            tmp.write(img_response.content)
                            tmp.close()
                            print(f"Downloaded YouTube thumbnail via API: {quality} quality")
                            return tmp.name
        except Exception as e:
            print(f"YouTube API thumbnail failed: {e}, trying direct...")

    # Fallback — direct thumbnail URL (no API needed)
    headers = {"User-Agent": "Mozilla/5.0"}
    for quality in ["maxresdefault", "hqdefault", "mqdefault", "default"]:
        try:
            thumb_url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
            response = requests.get(thumb_url, headers=headers, timeout=10)
            if response.status_code == 200 and len(response.content) > 5000:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp.write(response.content)
                tmp.close()
                return tmp.name
        except Exception:
            continue

    raise ValueError(f"Could not get YouTube thumbnail for video: {video_id}")


def get_instagram_media_direct(url: str) -> str:
    """
    Downloads Instagram image via RapidAPI or oEmbed.
    """
    import urllib.parse
    rapidapi_key = os.getenv("RAPIDAPI_KEY")

    # Clean the URL first — remove tracking params, ensure full URL
    # Handle case where user pastes just query params or partial URL
    if not url.startswith("http"):
        raise ValueError(
            "Invalid Instagram URL. Please paste the full URL "
            "like: https://www.instagram.com/p/ABC123/"
        )

    # Parse and clean URL — keep only the path
    parsed = urllib.parse.urlparse(url)
    clean_url = f"https://www.instagram.com{parsed.path.rstrip('/')}/"
    print(f"Cleaned Instagram URL: {clean_url}")

    # Extract shortcode from path
    # Handles: /p/ABC123/, /reel/ABC123/, /tv/ABC123/
    path_parts = [p for p in parsed.path.split("/") if p]
    if len(path_parts) < 2:
        raise ValueError(
            "Could not extract post ID from Instagram URL. "
            "Please use format: https://www.instagram.com/p/POST_ID/"
        )
    shortcode = path_parts[-1]  # last non-empty part is the shortcode
    print(f"Instagram shortcode: {shortcode}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Try RapidAPI with full URL
    if rapidapi_key:
        # Try multiple RapidAPI endpoints (different ones work at diff times)
        rapidapi_attempts = [
            {
                "url": "https://instagram-scraper-api2.p.rapidapi.com/v1/post_info",
                "host": "instagram-scraper-api2.p.rapidapi.com",
                "params": {"code_or_id_or_url": shortcode}
            },
            {
                "url": "https://instagram-scraper-api2.p.rapidapi.com/v1.2/post_info",
                "host": "instagram-scraper-api2.p.rapidapi.com",
                "params": {"code_or_id_or_url": clean_url}
            },
        ]

        for attempt in rapidapi_attempts:
            try:
                api_headers = {
                    "x-rapidapi-host": attempt["host"],
                    "x-rapidapi-key": rapidapi_key,
                    "User-Agent": "Mozilla/5.0"
                }
                response = requests.get(
                    attempt["url"],
                    headers=api_headers,
                    params=attempt["params"],
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()

                # Navigate response structure
                post_data = data.get("data", data)
                image_url = (
                    post_data.get("thumbnail_url") or
                    post_data.get("display_url") or
                    post_data.get("image_versions2", {})
                        .get("candidates", [{}])[0].get("url") or
                    post_data.get("image_versions", {})
                        .get("items", [{}])[0].get("url")
                )

                if image_url:
                    img_response = requests.get(
                        image_url, headers=headers, timeout=15
                    )
                    img_response.raise_for_status()
                    tmp = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".jpg"
                    )
                    tmp.write(img_response.content)
                    tmp.close()
                    print("Downloaded Instagram media via RapidAPI")
                    return tmp.name

            except Exception as e:
                print(f"RapidAPI attempt failed ({attempt['url']}): {e}")
                continue

    # Fallback 1 — oEmbed with clean URL
    try:
        oembed_url = f"https://www.instagram.com/oembed/?url={clean_url}"
        response = requests.get(oembed_url, headers=headers, timeout=15)
        response.raise_for_status()
        thumbnail_url = response.json().get("thumbnail_url")

        if thumbnail_url:
            img_response = requests.get(
                thumbnail_url, headers=headers, timeout=15
            )
            img_response.raise_for_status()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(img_response.content)
            tmp.close()
            print("Downloaded Instagram thumbnail via oEmbed")
            return tmp.name

    except Exception as e:
        print(f"oEmbed failed: {e}")

    # Fallback 2 — return helpful error with suggestion
    raise ValueError(
        f"Could not access Instagram post '{shortcode}'. "
        f"Instagram has restricted automated access. "
        f"Please download the image/video manually and use "
        f"the file upload option (/register) instead."
    )


def download_image_direct(url: str) -> str:
    """
    Direct HTTP download for plain image URLs with retry.
    """
    import time
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(
                url,
                stream=True,
                timeout=20,
                headers=headers
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "image" not in content_type and "octet-stream" not in content_type:
                raise ValueError(f"Not an image: {content_type}")

            ext = os.path.splitext(urlparse(url).path)[1].lower() or ".jpg"
            if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"]:
                ext = ".jpg"

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            
            # Read in chunks to handle incomplete reads
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
                    downloaded += len(chunk)
            tmp.close()

            # Validate file is large enough to be a real image
            if downloaded < 5000:
                os.unlink(tmp.name)
                raise ValueError(f"Downloaded file too small: {downloaded} bytes")

            return tmp.name

        except (requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError) as e:
            last_error = e
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise ValueError(f"Direct download failed: {e}")

        except Exception as e:
            raise ValueError(f"Direct download failed: {e}")

    raise ValueError(f"Direct download failed after retries: {last_error}")


def download_from_url(url: str) -> str:
    """
    Smart downloader — handles YouTube, Instagram, direct image URLs.
    """
    if not url or not url.startswith("http"):
        raise ValueError(
            f"Invalid URL: '{url}'. "
            f"Please provide a full URL starting with https://"
        )

    if is_blocked_domain(url):
        raise ValueError(f"Blocked domain, skipping: {url}")

    if is_youtube_url(url):
        return get_youtube_thumbnail_direct(url)

    if is_instagram_url(url):
        return get_instagram_media_direct(url)

    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"]:
        try:
            return download_image_direct(url)
        except Exception as e:
            raise ValueError(f"Direct download failed: {e}")

    raise ValueError(
        f"Unsupported URL. Supported: YouTube links, Instagram post "
        f"links, or direct image URLs (.jpg .png .webp etc). "
        f"For other platforms please upload the file directly."
    )


def upload_to_gcs(local_path: str, destination_blob: str) -> str:
    from google.cloud import storage
    client = storage.Client()
    bucket = client.bucket(os.getenv("BUCKET_NAME"))
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(local_path)
    return f"gs://{os.getenv('BUCKET_NAME')}/{destination_blob}"


def download_from_gcs(gcs_uri: str) -> str:
    from google.cloud import storage
    client = storage.Client()
    bucket_name = os.getenv("BUCKET_NAME")
    path = gcs_uri.replace(f"gs://{bucket_name}/", "")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(path)
    ext = os.path.splitext(path)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    blob.download_to_filename(tmp.name)
    return tmp.name


def cleanup_temp_files(*paths):
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass

def get_instagram_media_direct(url: str) -> str:
    """
    Downloads Instagram image/video thumbnail via RapidAPI.
    Uses 'Instagram Scraper Stable API' - Detailed Reel Data endpoint.
    """
    import urllib.parse
    rapidapi_key = os.getenv("RAPIDAPI_KEY")

    if not url.startswith("http"):
        raise ValueError(
            "Invalid Instagram URL. Please paste the full URL "
            "like: https://www.instagram.com/p/ABC123/"
        )

    # Clean URL
    parsed = urllib.parse.urlparse(url)
    clean_url = f"https://www.instagram.com{parsed.path.rstrip('/')}/"

    # Extract shortcode
    path_parts = [p for p in parsed.path.split("/") if p]
    if len(path_parts) < 2:
        raise ValueError(
            "Could not extract post ID. "
            "Use format: https://www.instagram.com/p/POST_ID/"
        )
    shortcode = path_parts[-1]
    print(f"Instagram shortcode: {shortcode}, clean URL: {clean_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    if rapidapi_key:
        try:
            # Use the working endpoint from your RapidAPI test
            api_url = "https://instagram-scraper-stable-api.p.rapidapi.com/get_media_data.php"
            api_headers = {
                "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
                "x-rapidapi-key": rapidapi_key
            }
            params = {
                "reel_post_code_or_url": clean_url,
                "type": "reel"  # works for both posts and reels
            }

            response = requests.get(
                api_url,
                headers=api_headers,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            print(f"RapidAPI response keys: {list(data.keys())[:5]}")

            # Based on your response data structure:
            # data has: thumbnail_src, display_url, video_url, display_resources
            image_url = (
                data.get("display_url") or          # highest quality image
                data.get("thumbnail_src") or         # thumbnail fallback
                # Try display_resources for highest res
                (data.get("display_resources", [{}])[-1].get("src")
                 if data.get("display_resources") else None)
            )

            if image_url:
                img_response = requests.get(
                    image_url, headers=headers, timeout=15
                )
                img_response.raise_for_status()

                # Validate it's actually an image
                content_type = img_response.headers.get("content-type", "")
                if "image" in content_type or len(img_response.content) > 5000:
                    tmp = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".jpg"
                    )
                    tmp.write(img_response.content)
                    tmp.close()
                    print(f"Downloaded Instagram image via RapidAPI: {len(img_response.content)} bytes")
                    return tmp.name

        except Exception as e:
            print(f"RapidAPI Instagram failed: {e}")

    # Fallback — page scrape with bot UA
    try:
        page_headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(clean_url, headers=page_headers, timeout=15)

        if response.status_code == 200:
            import re
            og_image = re.search(
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https[^"\']+)["\']',
                response.text
            )
            if not og_image:
                og_image = re.search(
                    r'content=["\'](https://[^"\']+\.jpg[^"\']*)["\'][^>]+property=["\']og:image["\']',
                    response.text
                )

            if og_image:
                image_url = og_image.group(1)
                img_response = requests.get(
                    image_url, headers=headers, timeout=15
                )
                img_response.raise_for_status()
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp.write(img_response.content)
                tmp.close()
                print("Downloaded Instagram image via page scrape")
                return tmp.name

    except Exception as e:
        print(f"Page scrape failed: {e}")

    raise ValueError(
        f"Could not access Instagram post. "
        f"Please download the image and upload directly using /register."
    )