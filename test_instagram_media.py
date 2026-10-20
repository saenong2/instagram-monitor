"""One-request, read-only Meta Business Discovery media capability test.

Does not modify existing dashboard or collection data. Never prints URLs/tokens.
"""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

API_VERSION = "v26.0"
USERNAME = "happycitysejong_official"


def main():
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("META_IG_USER_ID", "").strip()
    if not token or not ig_id.isdigit():
        raise RuntimeError("GitHub secrets META_ACCESS_TOKEN / META_IG_USER_ID missing or invalid")

    # At most ONE API request; test on the happiness-city account only.
    fields = (
        f"business_discovery.username({USERNAME})"
        "{username,media.limit(10)"
        "{id,media_type,media_url,thumbnail_url,"
        "children.limit(10){id,media_type,media_url,thumbnail_url}}}"
    )
    url = f"https://graph.facebook.com/{API_VERSION}/{ig_id}?" + urlencode(
        {"fields": fields, "access_token": token}
    )
    try:
        with urlopen(url, timeout=35) as response:
            result = json.load(response)
    except HTTPError as exc:
        # Do not expose the request URL, raw error body or credentials.
        try:
            api_code = json.load(exc).get("error", {}).get("code", "unknown")
        except (OSError, ValueError, AttributeError):
            api_code = "unknown"
        print(f"TEST FAILED: HTTP {exc.code}, Meta error code {api_code}")
        print("Media fields may not be supported for business discovery of another account.")
        return 1
    except (URLError, TimeoutError):
        print("TEST FAILED: network or timeout")
        return 1

    account = result.get("business_discovery") or {}
    posts = (account.get("media") or {}).get("data") or []
    print(f"Test account: {USERNAME}")
    print(f"Posts examined: {len(posts)}")
    print("Type | media_url? | thumbnail_url? | child_count | child_media_urls")
    for post in posts:
        children = (post.get("children") or {}).get("data") or []
        print(
            f"{post.get('media_type', 'UNKNOWN')} | "
            f"{bool(post.get('media_url'))} | "
            f"{bool(post.get('thumbnail_url'))} | "
            f"{len(children)} | "
            f"{sum(bool(child.get('media_url')) for child in children)}"
        )
    print("Read-only test completed. No files changed. No media URLs shown.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"TEST FAILED: {exc}")
        sys.exit(1)
