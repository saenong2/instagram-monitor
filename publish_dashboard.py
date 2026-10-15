"""Convert collected API output into the existing public dashboard JSON.

No credentials are read or written here. The collector handles Meta API access.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = Path('data/test_accounts.json')
DESTINATION = Path('dashboard.json')
KST = timezone(timedelta(hours=9))
ROSTER = Path('agencies.json')
# Historical names in previously published posts; keep them consistent after renames.
RENAMES = {
    '산업통상자원부': '산업통상부',
    '기후부(환경부)': '기후에너지환경부',
    '중소기업벤처부': '중소벤처기업부',
}


def roster_levels():
    data = read_json(ROSTER)
    if not isinstance(data.get('agencies'), list):
        raise RuntimeError('agencies.json missing or invalid; refusing to publish')
    return {a['name']: a['group'] for a in data['agencies'] if a.get('name') and a.get('group') in ('장관급','차관급','기타')}



def read_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    source = read_json(SOURCE)
    accounts = source.get('accounts', [])
    if not accounts:
        raise RuntimeError('No collected accounts; refusing to overwrite the dashboard')
    levels = roster_levels()
    collected = datetime.fromisoformat(source['collected_at'].replace('Z', '+00:00'))
    if collected.tzinfo is None:
        raise RuntimeError('Collection timestamp must include timezone')

    previous = read_json(DESTINATION)
    existing_posts = {str(p['id']): p for p in previous.get('posts', []) if p.get('id')}
    for old in existing_posts.values():
        old['agency'] = RENAMES.get(old.get('agency'), old.get('agency'))
        old['level'] = levels.get(old.get('agency'), old.get('level', '기타'))
    previous_at = previous.get('collected_at')
    if previous_at:
        prev_time = datetime.fromisoformat(previous_at.replace('Z', '+00:00'))
        interval_hours = (collected - prev_time).total_seconds() / 3600
        comparable = 18 <= interval_hours <= 36
    else:
        comparable = False

    agencies = []
    fresh_posts = {}
    for account in accounts:
        agency = account['agency']
        agency = RENAMES.get(agency, agency)
        if agency not in levels:
            raise RuntimeError(f'Collected agency not in agencies.json: {agency}')
        level = levels[agency]
        agencies.append({
            'name': agency,
            'username': account['username'],
            'level': level,
            'followers': account.get('followers_count', 0),
            'media_count': account.get('media_count', 0),
        })
        for media in account.get('media', []):
            media_id = str(media['id'])
            old = existing_posts.get(media_id, {})
            current_views = media.get('view_count')
            old_views = old.get('views')
            delta = None
            if comparable and current_views is not None and old_views is not None:
                delta = max(0, int(current_views) - int(old_views))
            timestamp = media.get('timestamp', '')
            fresh_posts[media_id] = {
                'id': media_id,
                'agency': agency,
                'level': level,
                'date': timestamp[:10],
                'timestamp': timestamp,
                'type': media.get('media_type', 'IMAGE'),
                'caption': media.get('caption', ''),
                'likes': media.get('like_count', 0),
                'comments': media.get('comments_count', 0),
                'views': current_views,
                'view_delta': delta,
                'thumbnail': media.get('thumbnail_url') or media.get('media_url') or '',
                'permalink': media.get('permalink', ''),
            }

    # Retain posts from earlier successful collections, without fabricating current KPIs.
    # Recent posts are refreshed, including their expiring image URLs.
    existing_posts.update(fresh_posts)
    posts = sorted(existing_posts.values(), key=lambda x: x.get('timestamp', ''), reverse=True)
    posts = [p for p in posts if p.get('date', '') >= '2026-01-01']

    local_date = collected.astimezone(KST).strftime('%Y-%m-%d %H:%M KST')
    output = {
        'collected_at': collected.isoformat(),
        'updated_at': local_date,
        'coverage_note': f'시험 운영: {len(agencies)}개 기관 수집. 하루 1회 갱신, 최근 게시물 중심으로 누적 저장합니다.',
        'agencies': agencies,
        'posts': posts,
    }
    DESTINATION.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Published {len(agencies)} accounts and {len(posts)} posts to {DESTINATION}')
    print('Daily view comparison:', 'available' if comparable else 'waiting for next daily collection')


if __name__ == '__main__':
    main()
