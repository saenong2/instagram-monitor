"""Offline integrity checks; does not contact Meta."""
import json
from pathlib import Path
from publish_dashboard import read_previous_posts

manifest = json.loads(Path('dashboard.json').read_text(encoding='utf-8'))
assert len(manifest['agencies']) > 0, 'Missing agencies'
posts = read_previous_posts(manifest)
assert posts, 'Missing posts'
ids = [str(p['id']) for p in posts]
assert len(ids) == len(set(ids)), 'Duplicate post IDs'
assert len(posts) == manifest.get('post_count', len(posts)), 'Unexpected post count'
for filename in manifest.get('post_files', []):
    size = Path(filename).stat().st_size
    assert size < 350_000, f'Archive too large: {filename} ({size} bytes)'
print(f'OK: {len(manifest["agencies"])} agencies, {len(posts)} posts, {len(manifest.get("post_files", []))} post archives')
