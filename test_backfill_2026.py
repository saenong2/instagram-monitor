"""Offline safety tests for the 2026 Instagram backfill.

Run: python -m unittest -v test_backfill_2026.py
These tests use synthetic posts and a fake fetch function: no Meta API calls.
"""
import copy
import unittest
from unittest.mock import patch

from backfill_2026 import (
    MAX_REQUESTS_PER_RUN,
    make_post,
    process_pages,
    validate_state,
)


TODAY = '2026-10-23'


def account(username='demo_agency'):
    return {'username': username, 'agency': '테스트기관', 'level': '장관급'}


def media(post_id, date='2026-03-01', views=100):
    return {
        'id': post_id,
        'timestamp': date + 'T12:00:00+0000',
        'media_type': 'VIDEO',
        'view_count': views,
        'caption': '모의 영상',
    }


class BackfillOfflineTests(unittest.TestCase):
    def setUp(self):
        self.sleep = patch('backfill_2026.time.sleep', return_value=None)
        self.sleep.start()
        self.addCleanup(self.sleep.stop)

    def test_request_budget_caps_each_run_at_eight(self):
        self.assertEqual(MAX_REQUESTS_PER_RUN, 8)
        called = []

        def fake_fetch(username, cursor):
            called.append(cursor)
            return [media('post-' + str(len(called)))], 'cursor-' + str(len(called))

        state, used, added = process_pages(
            [account()], {'account_index': 0, 'after': None}, {}, fake_fetch,
            today=TODAY,
        )
        self.assertEqual(used, 8)
        self.assertEqual(len(called), 8)
        self.assertEqual(added, 8)
        self.assertEqual(state['after'], 'cursor-8')
        self.assertFalse(state['complete'])

    def test_resume_on_next_run_uses_saved_cursor(self):
        calls = []

        def fake_fetch(username, cursor):
            calls.append(cursor)
            if cursor is None:
                return [media('video-1')], 'page-2'
            if cursor == 'page-2':
                return [media('video-2')], None
            self.fail('Unexpected cursor')

        stored = {}
        state, used1, added1 = process_pages(
            [account()], {'account_index': 0, 'after': None}, stored,
            fake_fetch, budget=1, today=TODAY,
        )
        self.assertEqual((used1, added1), (1, 1))
        self.assertEqual(state['after'], 'page-2')
        resumed, used2, added2 = process_pages(
            [account()], state, stored, fake_fetch, budget=1, today=TODAY,
        )
        self.assertEqual((used2, added2), (1, 1))
        self.assertEqual(calls, [None, 'page-2'])
        self.assertEqual(set(stored), {'video-1', 'video-2'})
        self.assertTrue(resumed['complete'])

    def test_existing_posts_are_not_overwritten_and_duplicates_skipped(self):
        old = make_post(media('existing', views=100), '테스트기관', '장관급', '2026-10-21')
        old['view_delta'] = 27
        old['view_history'] = {'2026-10-21': 100, '2026-10-22': 127}
        stored = {'existing': old}
        before = copy.deepcopy(old)

        def fake_fetch(username, cursor):
            return [media('existing', views=999), media('new', views=50), media('new', views=50)], None

        state, used, added = process_pages(
            [account()], {'account_index': 0, 'after': None}, stored,
            fake_fetch, budget=8, today=TODAY,
        )
        self.assertEqual((used, added), (1, 1))
        self.assertEqual(stored['existing'], before)
        self.assertEqual(stored['new']['view_history'], {TODAY: 50})
        self.assertIsNone(stored['new']['view_delta'])
        self.assertTrue(state['complete'])

    def test_posts_older_than_2026_stop_that_account(self):
        calls = []

        def fake_fetch(username, cursor):
            calls.append((username, cursor))
            if username == 'first':
                return [media('in-2026'), media('old', date='2025-12-31')], 'another-page'
            return [media('second-2026')], None

        stored = {}
        state, used, added = process_pages(
            [account('first'), account('second')],
            {'account_index': 0, 'after': None}, stored, fake_fetch,
            budget=8, today=TODAY,
        )
        self.assertEqual((used, added), (2, 2))
        self.assertEqual([x[0] for x in calls], ['first', 'second'])
        self.assertNotIn('old', stored)
        self.assertTrue(state['complete'])

    def test_completed_state_makes_no_requests(self):
        def forbidden_fetch(username, cursor):
            self.fail('Fetch should not be called after completion')

        state, used, added = process_pages(
            [account()], {'account_index': 1, 'after': None, 'complete': True},
            {}, forbidden_fetch, today=TODAY,
        )
        self.assertEqual((used, added), (0, 0))
        self.assertTrue(state['complete'])

    def test_invalid_cursor_is_rejected_before_fetch(self):
        with self.assertRaises(RuntimeError):
            validate_state({'account_index': 0, 'after': 'bad?cursor'}, 1)


if __name__ == '__main__':
    unittest.main()
