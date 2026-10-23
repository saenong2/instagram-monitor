"""Slow, resumable 2026 Business Discovery archive backfill.

This is separate from daily monitoring and never changes daily collected_at or KPIs.
API requests: at most MAX_REQUESTS_PER_RUN (default 8), with no retries.
Only new post IDs are inserted; current daily records and view_delta are untouched.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from collect_instagram import API_VERSION, load_accounts
from publish_dashboard import (
    DESTINATION, KST, RENAMES, read_json, read_previous_posts,
    roster_levels, write_post_archives,
)

STATE_PATH = Path('data/backfill_2026_state.json')
START_DATE = '2026-01-01'
PAGE_SIZE = 30
MAX_REQUESTS_PER_RUN = 8
SECONDS_BETWEEN_REQUESTS = 2
# Bound failed/malformed requests too; this is not increased by environment variables.
CURSOR_PATTERN = re.compile(r'^[A-Za-z0-9_+=/-]{1,1024}$')


def validate_state(state, account_count):
    if not isinstance(state, dict):
        raise RuntimeError('Invalid backfill state; refusing to start')
    index = state.get('account_index', 0)
    cursor = state.get('after')
    if type(index) is not int or not 0 <= index <= account_count:
        raise RuntimeError('Invalid account_index in backfill state')
    if cursor is not None and (not isinstance(cursor, str) or not CURSOR_PATTERN.fullmatch(cursor)):
        raise RuntimeError('Invalid page cursor in backfill state')
    return index, cursor


def fetch_page(ig_user_id, token, username, after=None):
    # Meta Business Discovery cursors must be placed on the nested media field.
    # Do not log token, URL or cursor.
    if after is not None and not CURSOR_PATTERN.fullmatch(after):
        raise RuntimeError('Unusable media cursor; stopped before requesting')
    media_edge = f'media.limit({PAGE_SIZE})'
    if after:
        media_edge += f'.after({after})'
    fields = (
        f'business_discovery.username({username})'
        '{'
        f'{media_edge}'
        '{id,caption,media_type,media_url,thumbnail_url,'
        'like_count,comments_count,view_count,permalink,timestamp,'
        'children.limit(20){id,media_type,media_url,thumbnail_url}}'
        '}'
    )
    url = f'https://graph.facebook.com/{API_VERSION}/{ig_user_id}?' + urlencode({
        'fields': fields, 'access_token': token,
    })
    try:
        with urlopen(url, timeout=35) as response:
            payload = json.load(response)
    except HTTPError as error:
        # No raw error payload or full URL in public logs.
        raise RuntimeError(f'Meta API HTTP {error.code}; stopped without retry') from None
    except (URLError, TimeoutError):
        raise RuntimeError('Meta API network error; stopped without retry') from None
    business = payload.get('business_discovery')
    if not isinstance(business, dict):
        raise RuntimeError('Business Discovery response missing; stopped')
    media = business.get('media') or {}
    if not isinstance(media, dict) or not isinstance(media.get('data'), list):
        raise RuntimeError('Business Discovery media page malformed; stopped')
    page = media['data']
    paging = media.get('paging') or {}
    next_cursor = (paging.get('cursors') or {}).get('after') if isinstance(paging, dict) else None
    has_next = isinstance(paging, dict) and bool(paging.get('next'))
    # Some responses expose only the after cursor. No next URL is ever followed.
    if not has_next and next_cursor and len(page) >= PAGE_SIZE:
        has_next = True
    if has_next and (not isinstance(next_cursor, str) or not CURSOR_PATTERN.fullmatch(next_cursor)):
        raise RuntimeError('Media paging cursor missing or invalid; stopped safely')
    return page, next_cursor if has_next else None


def make_post(media, agency, level, sample_date):
    timestamp = media.get('timestamp') or ''
    if not timestamp or not isinstance(media.get('id'), (str, int)):
        raise RuntimeError('Historical post lacks timestamp or ID')
    media_type = media.get('media_type', 'IMAGE')
    views = media.get('view_count')
    history = ({sample_date: int(views)} if media_type == 'VIDEO' and views is not None else {})
    children = media.get('children') or {}
    if not isinstance(children, dict):
        children = {}
    return {
        'id': str(media['id']), 'agency': agency, 'level': level,
        'date': timestamp[:10], 'timestamp': timestamp,
        'type': media_type, 'caption': media.get('caption', ''),
        'likes': media.get('like_count', 0), 'comments': media.get('comments_count', 0),
        'views': views, 'view_delta': None, 'view_history': history,
        'thumbnail': media.get('thumbnail_url') or media.get('media_url') or '',
        'video_url': (media.get('media_url') or '') if media_type == 'VIDEO' else '',
        'images': [c.get('media_url') or c.get('thumbnail_url') for c in children.get('data', [])
                   if isinstance(c, dict) and (c.get('media_url') or c.get('thumbnail_url'))],
        'permalink': media.get('permalink', ''),
    }


def process_pages(accounts, state, stored_posts, fetch, budget=MAX_REQUESTS_PER_RUN, today=None):
    """Pure-ish orchestration, testable with a fake fetch function; no file writes."""
    if today is None:
        today = datetime.now(KST).strftime('%Y-%m-%d')
    index, after = validate_state(state, len(accounts))
    count = 0
    added = 0
    while index < len(accounts) and count < budget:
        account = accounts[index]
        items, next_cursor = fetch(account['username'], after)
        count += 1
        old_boundary = False
        agency = RENAMES.get(account['agency'], account['agency'])
        for item in items:
            date = str(item.get('timestamp') or '')[:10]
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
                raise RuntimeError('Invalid timestamp in historical media')
            if date < START_DATE:
                old_boundary = True
                continue
            if date > today:
                continue
            media_id = str(item.get('id') or '')
            if media_id and media_id not in stored_posts:
                stored_posts[media_id] = make_post(item, agency, account['level'], today)
                added += 1
        if old_boundary or not next_cursor:
            index += 1
            after = None
        else:
            if next_cursor == after:
                raise RuntimeError('Pagination cursor did not advance; stopped safely')
            after = next_cursor
        if count < budget and index < len(accounts):
            time.sleep(SECONDS_BETWEEN_REQUESTS)
    return {'account_index': index, 'after': after, 'complete': index == len(accounts)}, count, added


def main():
    manifest = read_json(DESTINATION)
    if not isinstance(manifest.get('post_files'), list):
        raise RuntimeError('Missing monthly archive manifest; no API calls made')
    posts = read_previous_posts(manifest)
    stored_posts = {str(p['id']): p for p in posts if p.get('id')}
    if len(stored_posts) != len(posts):
        raise RuntimeError('Duplicate or missing archived IDs; no API calls made')
    levels = roster_levels()
    roster = load_accounts()
    accounts = []
    for row in roster:
        agency = RENAMES.get(row['agency'], row['agency'])
        if agency not in levels:
            raise RuntimeError(f'Unknown agency in roster: {agency}')
        accounts.append({**row, 'level': levels[agency]})
    state = read_json(STATE_PATH) if STATE_PATH.exists() else {'account_index': 0, 'after': None}
    validate_state(state, len(accounts))
    if state.get('complete'):
        print('2026 backfill already complete; no API calls made.')
        return
    token = os.getenv('META_ACCESS_TOKEN', '').strip()
    ig_user_id = os.getenv('META_IG_USER_ID', '').strip()
    if not token or not ig_user_id.isdigit():
        raise RuntimeError('Missing/invalid Meta secrets; no API calls made')
    def fetch(username, cursor):
        return fetch_page(ig_user_id, token, username, cursor)
    updated, used, added = process_pages(accounts, state, stored_posts, fetch)
    # Write only after ALL API calls have succeeded (no partial state on API errors).
    all_posts = sorted(stored_posts.values(), key=lambda p: p.get('timestamp') or '', reverse=True)
    filenames = write_post_archives(all_posts)
    manifest['post_files'] = filenames
    manifest['post_count'] = len(all_posts)
    # Do not alter collected_at / updated_at / agencies / today's view_delta.
    DESTINATION.write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Backfill: {used} API calls, {added} new posts; account {updated["account_index"]}/{len(accounts)}; completed={updated["complete"]}')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError) as error:
        sys.exit(f'Backfill stopped safely: {error}')
