"""Two-account Meta Business Discovery smoke test. No token is written to output."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

API_VERSION = "v26.0"
ACCOUNTS = [
    {"agency": "농림축산식품부", "username": "nong_ru_wahhhhh"},
    {"agency": "행정안전부", "username": "withyou3542"},
]
OUTPUT_PATH = Path("data/test_accounts.json")


def fetch_account(ig_user_id, token, agency, username):
    fields = (
        f"business_discovery.username({username})"
        "{username,followers_count,media_count,"
        "media.limit(10){id,caption,media_type,media_url,thumbnail_url,"
        "like_count,comments_count,view_count,permalink,timestamp}}"
    )
    url = (
        f"https://graph.facebook.com/{API_VERSION}/{ig_user_id}?"
        + urlencode({"fields": fields, "access_token": token})
    )
    try:
        with urlopen(url, timeout=35) as response:
            payload = json.load(response)
    except HTTPError as error:
        try:
            details = json.load(error)
            api_error = details.get("error", {})
            message = api_error.get("message", "Unknown API error")
            code = api_error.get("code", "unknown")
        except (ValueError, OSError):
            message, code = "Unable to read API error", "unknown"
        raise RuntimeError(f"{agency}: Meta API error {code}: {message}") from None
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"{agency}: network connection failed ({type(error).__name__})") from None

    data = payload.get("business_discovery")
    if not isinstance(data, dict):
        raise RuntimeError(f"{agency}: no business_discovery data returned")
    return {
        "agency": agency,
        "username": data.get("username", username),
        "followers_count": data.get("followers_count"),
        "media_count": data.get("media_count"),
        "media": data.get("media", {}).get("data", []),
    }


def main():
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("META_IG_USER_ID", "").strip()
    if not token or not ig_id:
        sys.exit("Missing required GitHub secrets META_ACCESS_TOKEN or META_IG_USER_ID")
    if not ig_id.isdigit():
        sys.exit("META_IG_USER_ID must be the numeric Instagram business account ID")

    accounts = []
    for item in ACCOUNTS:
        account = fetch_account(ig_id, token, item["agency"], item["username"])
        accounts.append(account)
        print(f"OK: {item['agency']} - {len(account['media'])} recent posts")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {"collected_at": datetime.now(timezone.utc).isoformat(), "accounts": accounts},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        sys.exit(str(error))
