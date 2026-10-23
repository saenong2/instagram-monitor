"""No-network tests for 2026 backfill safety, resumability and deduplication."""
import unittest
from unittest.mock import patch
from backfill_2026 import process_pages, validate_state


def media(ident, date):
    return {'id': str(ident), 'timestamp': date + 'T01:00:00+0000', 'media_type': 'VIDEO', 'view_count': 100}


class BackfillTests(unittest.TestCase):
    def setUp(self):
        self.accounts = [
            {'agency': '기관A', 'username': 'agency_a', 'level': '장관급'},
            {'agency': '기관B', 'username': 'agency_b', 'level': '차관급'},
        ]

    @patch('backfill_2026.time.sleep', lambda _: None)
    def test_budget_and_resume_and_preservation(self):
        existing = {'3': {'id': '3', 'view_history': {'2026-10-20': 55}, 'view_delta': 99}}
        calls = []
        def fetch(username, cursor):
            calls.append((username, cursor))
            if username == 'agency_a' and cursor is None:
                return [media(1, '2026-10-01'), media(3, '2026-10-01')], 'nextcursor'
            if username == 'agency_a' and cursor == 'nextcursor':
                return [media(2, '2026-01-03'), media(0, '2025-12-31')], None
            return [media(4, '2026-06-01')], None
        state, count, added = process_pages(self.accounts, {}, existing, fetch, budget=1, today='2026-10-23')
        self.assertEqual((count, added), (1, 1))
        self.assertEqual(state['after'], 'nextcursor')
        self.assertEqual(existing['3']['view_delta'], 99)
        state, count, added = process_pages(self.accounts, state, existing, fetch, budget=2, today='2026-10-23')
        self.assertEqual((count, added), (2, 2))
        self.assertTrue(state['complete'])
        self.assertNotIn('0', existing)
        self.assertEqual(calls, [('agency_a', None), ('agency_a', 'nextcursor'), ('agency_b', None)])
        self.assertEqual(existing['1']['view_delta'], None)
        self.assertEqual(existing['1']['view_history'], {'2026-10-23': 100})

    def test_bad_state_rejected(self):
        for state in ({'account_index': -1}, {'account_index': '0'}, {'after': 'bad)'}, {'account_index': 100}):
            with self.assertRaises(RuntimeError):
                validate_state(state, 2)

    def test_repeat_cursor_stopped(self):
        with self.assertRaises(RuntimeError):
            process_pages(self.accounts, {'account_index': 0, 'after': 'abc'}, {},
                          lambda *_: ([media(1, '2026-10-01')], 'abc'), budget=1,
                          today='2026-10-23')


if __name__ == '__main__':
    unittest.main()
