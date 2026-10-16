"""Collect verified Instagram accounts using Meta Business Discovery.

Safety defaults: 30 accounts, at most 30 API requests, no pagination.
Keeps the existing data/test_accounts.json schema for publish_dashboard.py.
Secrets are read only from environment variables.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

API_VERSION = "v26.0"
ROSTER_PATH = Path("agencies.json")
OUTPUT_PATH = Path("data/test_accounts.json")
MAX_ACCOUNTS_PER_RUN = 30
MAX_API_REQUESTS_PER_RUN = 30
POSTS_PER_ACCOUNT = 10
SECONDS_BETWEEN_REQUESTS = 2


def load_accounts():
    if not ROSTER_PATH.is_file():
        raise RuntimeError("agencies.json not found in repository root")
    try:
        roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RuntimeError("Unable to read agencies.json") from error

    if not isinstance(roster, dict) or not isinstance(roster.get("agencies"), list):
        raise RuntimeError("agencies.json must contain an agencies list")

    selected = []
    seen = set()
    for item in roster["agencies"]:
        if not isinstance(item, dict) or item.get("instagram_verified") is not True:
            continue
        name = item.get("name")
        username = item.get("instagram_username")
        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(username, str) or not username.strip():
            continue
        username = username.strip()
        if not all(ch.isascii() and (ch.isalnum() or ch in "._") for ch in username):
            raise RuntimeError(f"Invalid Instagram username for {name}")
        if username.lower() in seen:
            continue
        seen.add(username.lower())
        selected.append({"agency": name, "username": username})

    if not selected:
        raise RuntimeError("No verified Instagram accounts in agencies.json")
    if len(selected) > MAX_ACCOUNTS_PER_RUN or len(selected) > MAX_API_REQUESTS_PER_RUN:
        raise RuntimeError(
            f"Safety limit: {len(selected)} verified accounts, but at most "
            f"{min(MAX_ACCOUNTS_PER_RUN, MAX_API_REQUESTS_PER_RUN)} can be queried. "
            "No API calls were made. Expand only after testing."
        )
    return selected


def fetch_account(ig_user_id, token, agency, username):
    fields = (
        f"business_discovery.username({username})"
        "{username,followers_count,media_count,"
        f"media.limit({POSTS_PER_ACCOUNT})"
        "{id,caption,media_type,media_url,thumbnail_url,"
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
            code = details.get("error", {}).get("code", "unknown")
        except (ValueError, OSError, AttributeError):
            code = "unknown"
        # Never print token, URL, or raw API error body to logs.
        raise RuntimeError(
            f"{agency}: Meta API HTTP {error.code}, code {code}; "
            "stopped without retrying."
        ) from None
    except (URLError, TimeoutError):
        raise RuntimeError(f"{agency}: network error; stopped without retrying") from None

    data = payload.get("business_discovery")
    if not isinstance(data, dict):
        raise RuntimeError(f"{agency}: no business_discovery data; stopped")
    media = data.get("media") or {}
    return {
        "agency": agency,
        "username": data.get("username", username),
        "followers_count": data.get("followers_count"),
        "media_count": data.get("media_count"),
        "media": media.get("data", []) if isinstance(media, dict) else [],
    }


def main():
    # Read and validate roster *before* making any external API request.
    accounts_to_fetch = load_accounts()
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("META_IG_USER_ID", "").strip()
    if not token or not ig_id:
        raise RuntimeError("Missing GitHub secrets META_ACCESS_TOKEN or META_IG_USER_ID")
    if not ig_id.isdigit():
        raise RuntimeError("META_IG_USER_ID must be a numeric Instagram account ID")

    accounts = []
    for i, item in enumerate(accounts_to_fetch):
        if i:
            time.sleep(SECONDS_BETWEEN_REQUESTS)
        account = fetch_account(ig_id, token, item["agency"], item["username"])
        accounts.append(account)
        print(f"OK: {item['agency']} - {len(account['media'])} recent posts")

    # Only replace the data file if ALL requests succeeded.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "accounts": accounts,
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved: {OUTPUT_PATH} ({len(accounts)} accounts)")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        sys.exit(str(error))
