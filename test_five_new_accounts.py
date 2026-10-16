"""Manual-only check of five additional public Instagram professional accounts.

Does not modify dashboard data or GitHub files. Uses up to 5 Business Discovery
requests, with no pagination and no retries. Tokens are never printed.
"""
import json
import os
import sys
import time
from pathlib import Path

from collect_instagram import fetch_account

TARGETS = [
    ("방위사업청", "dapa_korea_official"),
    ("식품의약품안전처", "mfdskorea"),
    ("농촌진흥청", "rdakorea"),
    ("기상청", "kma_skylove"),
    ("국가유산청", "chlove_u"),
]


def main():
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("META_IG_USER_ID", "").strip()
    if not token or not ig_id.isdigit():
        raise RuntimeError("GitHub secrets META_ACCESS_TOKEN and META_IG_USER_ID are required")

    roster = json.loads(Path("agencies.json").read_text(encoding="utf-8"))
    listed = {item["name"]: item.get("instagram_username") for item in roster["agencies"]}
    for agency, username in TARGETS:
        if listed.get(agency) != username:
            raise RuntimeError(f"Account list mismatch for {agency}. No requests were made.")

    for number, (agency, username) in enumerate(TARGETS):
        if number:
            time.sleep(2)
        try:
            result = fetch_account(ig_id, token, agency, username)
        except RuntimeError as error:
            print(f"FAILED: {agency} (@{username}): {error}", file=sys.stderr)
            sys.exit("Stopped on first error; no dashboard files changed.")
        print(f"OK: {agency} (@{username}), recent posts: {len(result.get('media', []))}")

    print("SUCCESS: all five accounts accessible. No dashboard files changed.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        sys.exit(str(error))
