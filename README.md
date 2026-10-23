# 정부부처 인스타그램 모니터링

GitHub Pages에서 동작하는 대시보드입니다. Meta 토큰을 브라우저 파일에 넣지 마세요.

## 파일 구조

- `index.html`: 화면 마크업
- `styles.css`: 화면 디자인
- `app.js`: 검색, 성과 비교, 엑셀 다운로드, 상태 표시
- `dashboard.json`: 마지막 수집 시각, 기관 정보, 게시물 파일 목록
- `data/posts-2026-MM-NN.json`: 월별 게시물 보관용 분할 파일 (조회수 이력 포함)
- `collect_instagram.py`: 하루 1회 Meta API 수집
- `publish_dashboard.py`: 기존 이력을 보존하며 분할 파일 갱신
- `check_dashboard.py`: 수집 없이 저장 데이터 무결성 검사

## 수정할 때

1. `index.html`, `styles.css`, `app.js` 중 목적에 맞는 파일만 수정하세요.
2. GitHub Actions의 **Check Dashboard Files** 검사 결과를 확인하세요.
3. 대시보드 화면에서 검색/비교/다운로드/집계기간 표시를 확인하세요.

일일 자동 업데이트는 `.github/workflows/update-instagram.yml`에서 수행합니다. `dashboard.json`과 게시물 분할 파일은 자동 생성되므로 수동 편집하지 않는 편이 안전합니다.

## 중요: 첫 배포

이 ZIP은 기존 데이터와 코드를 모두 담고 있습니다. ZIP 내부 파일 **전체**를 동일한 저장소에 한 번에 반영하세요. `dashboard.json`만 먼저 교체하거나 게시물 분할 파일을 빠뜨리면 홈페이지가 데이터를 표시하지 못합니다. 변경 전 기존 저장소 ZIP을 보관하세요. Meta API를 새로 호출할 필요는 없습니다.

## 2026 historical post backfill (new, limited rollout)

- `backfill_2026.py` crawls 2026 posts using nested Business Discovery `media.after(cursor)` pagination, preserving all current daily post fields, video history, ranking deltas, profile metrics and current dashboard collection time. It **does not** perform the monthly recheck; that is a separate future task.
- `.github/workflows/backfill-instagram-2026.yml` is scheduled once per day at **20:40 KST**, on the **default branch only** after this update is merged. **Maximum eight Meta API requests per run**, no automatic retries, two-second pause between requests. The ordinary 07:00 KST daily job remains independent (51 requests as previously configured) and uses the same concurrency group to avoid simultaneous writes.
- `data/backfill_2026_state.json` stores `account_index`, `after` and `complete`. This is created by the first successful backfill run; after completion future scheduled runs do not call the API. If an API error or expired cursor occurs, the job stops, rather than issuing extra requests or silently skipping content. Check GitHub Actions if backfill stalls.
- **After each run** both the state file and monthly post archives must be committed. The original daily dashboard `collected_at`, per-day `view_delta`, and records for already known IDs are not changed by historical collection. Newly backfilled video views are a one-time collection-date baseline, not reconstructed historic daily values.
- Offline validation without credentials/network: `python -m unittest -v test_backfill_offline.py && python check_dashboard.py && node --check app.js`.
- **Important**: Native API may not expose every old post, may reject cursors, and may not return view counts for all third-party videos. 2026 completeness is only established after all accounts have successfully paginated to pre-2026 posts. Do not assume a complete archive from `complete: true` if an account API truncates pagination.
- Never commit Meta tokens; repository is publicly accessible.
