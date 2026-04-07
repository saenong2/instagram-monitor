import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
AGENCIES_FILE = DATA_DIR / "agencies.json"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
POSTS_FILE = DATA_DIR / "posts.json"
LAST_UPDATED_FILE = DATA_DIR / "last_updated.json"

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.instagram.com/",
        "X-IG-App-ID": "936619743392459",
    }
)


def load_agencies():
    with open(AGENCIES_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, dict) and "agencies" in raw:
        return raw["agencies"]
    return raw


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def safe_int(value):
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_timestamp(ts):
    if not ts:
        return ""
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        ts = str(ts)
        return ts[:10] if len(ts) >= 10 else ""


def detect_type(media):
    media_type = str(media.get("media_type") or media.get("__typename") or "").upper()
    product_type = str(media.get("product_type") or "").upper()

    if "REEL" in media_type or product_type == "CLIPS":
        return "reel"
    if "CAROUSEL" in media_type or "SIDECAR" in media_type:
        return "carousel"
    return "feed"


def extract_caption(media):
    caption = media.get("caption")
    if isinstance(caption, dict):
        text = caption.get("text", "")
        return text[:180]

    if isinstance(caption, str):
        return caption[:180]

    edge_caption = media.get("edge_media_to_caption", {})
    edges = edge_caption.get("edges", []) if isinstance(edge_caption, dict) else []
    if edges:
        node = edges[0].get("node", {})
        return str(node.get("text", ""))[:180]

    return ""


def extract_comments(media):
    for key in [
        "comment_count",
        "comments_count",
        "edge_media_to_comment",
        "edge_media_preview_comment",
    ]:
        value = media.get(key)

        if isinstance(value, int):
            return value

        if isinstance(value, dict):
            count = value.get("count")
            if isinstance(count, int):
                return count

    return None


def extract_likes(media):
    for key in [
        "like_count",
        "likes_count",
        "edge_media_preview_like",
        "edge_liked_by",
    ]:
        value = media.get(key)

        if isinstance(value, int):
            return value

        if isinstance(value, dict):
            count = value.get("count")
            if isinstance(count, int):
                return count

    return None


def extract_thumbnail(media):
    for key in ["thumbnail_url", "display_url", "image_versions2", "media_url"]:
        value = media.get(key)

        if isinstance(value, str) and value:
            return value

        if isinstance(value, dict):
            candidates = value.get("candidates", [])
            if candidates and isinstance(candidates, list):
                first = candidates[0]
                if isinstance(first, dict) and first.get("url"):
                    return first["url"]

    if isinstance(media.get("thumbnail_resources"), list) and media["thumbnail_resources"]:
        last = media["thumbnail_resources"][-1]
        if isinstance(last, dict) and last.get("src"):
            return last["src"]

    return ""


def extract_permalink(media, username):
    code = media.get("code") or media.get("shortcode")
    if code:
        return f"https://www.instagram.com/p/{code}/"

    permalink = media.get("permalink")
    if permalink:
        return permalink

    return f"https://www.instagram.com/{username}/"


def parse_profile_from_html(html):
    """
    HTML 백업용 파서.
    follower/post 수만 최소한 추출.
    """
    result = {
        "followers": None,
        "post_count": None,
    }

    meta_desc_match = re.search(
        r'content="([^"]*Followers[^"]*Posts[^"]*)"',
        html,
        flags=re.IGNORECASE,
    )
    if meta_desc_match:
        desc = meta_desc_match.group(1)
        number_matches = re.findall(r"([\d,.]+[MK]?)", desc, flags=re.IGNORECASE)
        if len(number_matches) >= 2:
            result["followers"] = compact_number_to_int(number_matches[0])
            result["post_count"] = compact_number_to_int(number_matches[1])

    return result


def compact_number_to_int(value):
    if value is None:
        return None

    s = str(value).strip().upper().replace(",", "")
    try:
        if s.endswith("K"):
            return int(float(s[:-1]) * 1000)
        if s.endswith("M"):
            return int(float(s[:-1]) * 1000000)
        return int(float(s))
    except Exception:
        return None


def fetch_profile_info(username):
    """
    1차: web_profile_info 비공식 공개 엔드포인트
    2차: HTML 백업
    """
    url = "https://www.instagram.com/api/v1/users/web_profile_info/"
    params = {"username": username}

    try:
        res = SESSION.get(url, params=params, timeout=30)
        if res.status_code == 200:
            data = res.json()
            user = data.get("data", {}).get("user", {})
            if user:
                return {"mode": "api", "user": user}
    except Exception:
        pass

    # 백업: 프로필 HTML
    html_url = f"https://www.instagram.com/{username}/"
    res = SESSION.get(html_url, timeout=30)
    res.raise_for_status()

    backup = parse_profile_from_html(res.text)
    return {
        "mode": "html",
        "user": {
            "username": username,
            "full_name": username,
            "follower_count": backup.get("followers"),
            "edge_followed_by": {"count": backup.get("followers")},
            "edge_owner_to_timeline_media": {"count": backup.get("post_count"), "edges": []},
            "profile_pic_url_hd": "",
        },
    }


def build_account_from_user(agency, user):
    followers = (
        safe_int(user.get("follower_count"))
        or safe_int((user.get("edge_followed_by") or {}).get("count"))
        or 0
    )

    post_count = (
        safe_int(user.get("media_count"))
        or safe_int((user.get("edge_owner_to_timeline_media") or {}).get("count"))
        or 0
    )

    edges = (user.get("edge_owner_to_timeline_media") or {}).get("edges", [])
    last_upload = ""
    if edges:
        node = edges[0].get("node", {})
        ts = node.get("taken_at_timestamp") or node.get("taken_at")
        last_upload = parse_timestamp(ts)

    return {
        "agency": agency["agency"],
        "display_name": agency.get("display_name", agency["agency"]),
        "instagram": agency["instagram"],
        "url": agency["url"],
        "level": agency["level"],
        "followers": followers,
        "post_count": post_count,
        "weekly_posts": None,
        "last_upload": last_upload,
        "profile_picture_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url") or "",
    }


def extract_media_list(user):
    # 신형 응답
    timeline = user.get("edge_owner_to_timeline_media", {})
    if isinstance(timeline, dict) and isinstance(timeline.get("edges"), list):
        return [edge.get("node", {}) for edge in timeline["edges"] if isinstance(edge, dict)]

    # 다른 형태 백업
    if isinstance(user.get("media"), list):
        return user["media"]

    return []


def build_posts_from_user(agency, user):
    posts = []
    username = agency["instagram"]
    media_list = extract_media_list(user)

    for media in media_list[:6]:
        ts = media.get("taken_at_timestamp") or media.get("taken_at") or media.get("timestamp")
        posts.append(
            {
                "agency": agency["agency"],
                "display_name": agency.get("display_name", agency["agency"]),
                "instagram": agency["instagram"],
                "url": agency["url"],
                "level": agency["level"],
                "date": parse_timestamp(ts),
                "type": detect_type(media),
                "caption": extract_caption(media),
                "thumbnail": extract_thumbnail(media),
                "link": extract_permalink(media, username),
                "views": safe_int(media.get("view_count")) or safe_int(media.get("play_count")),
                "likes": extract_likes(media),
                "comments": extract_comments(media),
                "timestamp_raw": ts or "",
            }
        )

    return posts


def build_outputs(agencies):
    accounts = []
    posts = []

    for idx, agency in enumerate(agencies, start=1):
        if not agency.get("active", True):
            continue

        username = agency["instagram"]

        try:
            print(f"[{idx}] 수집 중: {agency['agency']} (@{username})")
            profile = fetch_profile_info(username)
            user = profile["user"]

            account = build_account_from_user(agency, user)
            account["source_mode"] = profile["mode"]
            accounts.append(account)

            post_items = build_posts_from_user(agency, user)
            for p in post_items:
                p["source_mode"] = profile["mode"]
            posts.extend(post_items)

        except Exception as e:
            print(f"[WARN] {agency['agency']} 수집 실패: {e}")

        time.sleep(2)

    accounts.sort(
        key=lambda x: (
            0 if x["level"] == "장관급" else 1,
            -int(x.get("followers") or 0),
            x["agency"],
        )
    )

    posts.sort(key=lambda x: str(x.get("timestamp_raw") or ""), reverse=True)

    for p in posts:
        p.pop("timestamp_raw", None)

    return accounts, posts


def main():
    agencies = load_agencies()
    accounts, posts = build_outputs(agencies)

    save_json(ACCOUNTS_FILE, accounts)
    save_json(POSTS_FILE, posts)
    save_json(
        LAST_UPDATED_FILE,
        {
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "accounts_count": len(accounts),
            "posts_count": len(posts),
            "mode": "public_profile_scrape",
        },
    )

    print(f"accounts.json 저장 완료: {len(accounts)}건")
    print(f"posts.json 저장 완료: {len(posts)}건")


if __name__ == "__main__":
    main()
