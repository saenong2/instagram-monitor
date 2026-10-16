"""Manually test the 16 not-yet-enabled Instagram accounts, without publishing.

Retains the existing Test Five Instagram Accounts GitHub Actions workflow filename.
Uses up to 16 Business Discovery calls, 2 seconds apart; no pagination/retries.
Continues after account-specific errors, but stops early if rate limited.
Never logs credentials, URLs or raw Meta responses.
"""
import json
import os
import sys
import time
from pathlib import Path

from collect_instagram import fetch_account

ROSTER_PATH = Path("agencies.json")
EXPECTED_ALREADY_VERIFIED = 35
EXPECTED_TO_TEST = 16
RATE_LIMIT_CODES = ("code 4;", "code 17;", "code 32;", "code 613;", "HTTP 429,")


def main():
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    agencies = roster.get("agencies")
    if not isinstance(agencies, list):
        raise RuntimeError("agencies.json has no agencies list. No requests made.")

    verified = [a for a in agencies if a.get("instagram_verified") is True]
    targets = [a for a in agencies if a.get("instagram_verified") is not True]
    if len(agencies) != 51 or len(verified) != EXPECTED_ALREADY_VERIFIED or len(targets) != EXPECTED_TO_TEST:
        raise RuntimeError("Expected 51 accounts (35 enabled + 16 remaining). No requests made.")
    if any(not isinstance(a.get("instagram_username"), str) or
           not a["instagram_username"].strip() or
           not isinstance(a.get("name"), str) or not a["name"].strip()
           for a in targets):
        raise RuntimeError("Missing agency name or username. No requests made.")

    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ig_id = os.getenv("META_IG_USER_ID", "").strip()
    if not token or not ig_id.isdigit():
        raise RuntimeError("Missing valid GitHub Meta secrets. No requests made.")

    print(f"Testing {len(targets)} remaining accounts (maximum 16 requests).", flush=True)
    successes = []
    failures = []
    for index, item in enumerate(targets):
        if index:
            time.sleep(2)
        agency = item["name"]
        username = item["instagram_username"]
        try:
            result = fetch_account(ig_id, token, agency, username)
        except RuntimeError as exc:
            # fetch_account sanitizes its errors; no URLs or access tokens.
            error = str(exc)
            failures.append((agency, username, error))
            print(f"FAILED: {agency} (@{username}) - {error}", flush=True)
            if any(flag in error for flag in RATE_LIMIT_CODES):
                print("STOPPED: possible rate limit. No more API requests.", flush=True)
                break
            continue
        successes.append((agency, username))
        print(f"OK: {agency} (@{username}), recent posts: {len(result.get('media', []))}", flush=True)

    print("\n=== RESULT SUMMARY ===", flush=True)
    print(f"OK {len(successes)} / FAILED {len(failures)} / NOT TESTED {len(targets) - len(successes) - len(failures)}", flush=True)
    print("SUCCESSFUL: " + (", ".join(name for name, _ in successes) or "none"), flush=True)
    if failures:
        print("FAILED: " + ", ".join(name for name, _, _ in failures), flush=True)
    print("No dashboard files were changed.", flush=True)
    if failures or len(successes) != len(targets):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, TypeError) as error:
        sys.exit(str(error))
