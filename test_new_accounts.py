"""Manual-only, two-account Meta Business Discovery test.

Does not write dashboard.json or data/test_accounts.json.
Credentials must be supplied as GitHub Actions secrets via environment.
"""
import os
import sys

from collect_instagram import fetch_account

TARGETS = [
    ("재정경제부", "mofekorea"),
    ("기획예산처", "mpbkorea"),
]


def main():
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    ig_id = os.environ.get("META_IG_USER_ID", "").strip()
    if not token or not ig_id.isdigit():
        raise RuntimeError("GitHub secrets META_ACCESS_TOKEN and META_IG_USER_ID are required")

    passed = 0
    for agency, username in TARGETS:
        try:
            result = fetch_account(ig_id, token, agency, username)
            count = len(result.get("media", []))
            print(f"OK: {agency} (@{username}), recent posts: {count}")
            passed += 1
        except RuntimeError as error:
            print(f"FAILED: {agency} (@{username}): {error}", file=sys.stderr)
            # Fail fast, without retrying or making another API request.
            break

    if passed != len(TARGETS):
        sys.exit("Account check failed. No dashboard files were changed.")
    print("Both new accounts are accessible. No dashboard files were changed.")


if __name__ == "__main__":
    main()
