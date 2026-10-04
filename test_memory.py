import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from agent import Agent
from demo import run
from memory import MemoryStore


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'memory.db'
        self.store = MemoryStore(self.path)
        self.travel = Agent('travel', '17', self.store)
        self.food = Agent('food', '17', self.store)

    def test_empty(self):
        self.assertIsNone(self.food.recall())

    def test_save_and_share(self):
        self.travel.remember('매운 음식을 못 먹음')
        self.assertEqual(self.food.recall(), '매운 음식을 못 먹음')

    def test_user_separation(self):
        self.travel.remember('민지의 기억')
        other = Agent('food', '99', self.store)
        other.remember('다른 사용자의 기억')
        self.assertEqual(self.food.recall(), '민지의 기억')
        self.assertEqual(other.recall(), '다른 사용자의 기억')

    def test_restart_and_other_agent_in_separate_processes(self):
        run(self.path, 'travel', '17', 'remember', '매운 음식을 못 먹음')
        self.assertEqual(run(self.path, 'food', '17', 'read'),
                         {'memory': '매운 음식을 못 먹음'})

    def test_subprocess_forces_utf8(self):
        with patch.dict(os.environ, {'PYTHONIOENCODING': 'cp949'}):
            run(self.path, 'travel', '17', 'remember', '순한 음식 선호 🌶️')
            self.assertEqual(run(self.path, 'food', '17', 'read'),
                             {'memory': '순한 음식 선호 🌶️'})

    def test_context_before_and_after(self):
        before = self.food.prepare('저녁 뭐 먹을까?')
        self.travel.remember('순한 음식 선호')
        after = self.food.prepare('저녁 뭐 먹을까?')
        self.assertIsNone(json.loads(before[1]['content'])['참고 메모'])
        self.assertEqual(json.loads(after[1]['content'])['참고 메모'], '순한 음식 선호')
        self.assertEqual(json.loads(after[1]['content'])['현재 질문'], '저녁 뭐 먹을까?')

    def test_update_replaces_same_topic(self):
        self.travel.remember('매운 음식을 못 먹음')
        self.travel.remember('약간 매운 음식 가능')
        self.assertEqual(self.food.recall(), '약간 매운 음식 가능')
        self.assertEqual(len(self.store.list_for('17')), 1)

    def test_new_topic_does_not_replace_old(self):
        self.travel.remember('매운 음식을 못 먹음')
        self.travel.remember('기차 선호', 'transport_preference')
        self.assertEqual(len(self.store.list_for('17')), 2)
        self.assertEqual(self.food.recall(), '매운 음식을 못 먹음')

    def test_delete_is_scoped_and_repeat_safe(self):
        self.travel.remember('민지의 기억')
        Agent('travel', '99', self.store).remember('다른 기억')
        self.assertTrue(self.travel.forget())
        self.assertFalse(self.travel.forget())
        self.assertIsNone(self.food.recall())
        self.assertEqual(self.store.read('99', 'food_preference'), '다른 기억')

    def test_search_literal_and_scoped(self):
        self.travel.remember('매운 음식은 피함')
        Agent('travel', '99', self.store).remember('매운 음식 좋아함')
        self.assertEqual(len(self.store.search('17', '매운')), 1)
        self.assertEqual(self.store.search('17', 'spicy'), [])
        self.assertEqual(self.store.search('17', '%'), [])

    def test_parameterized_sql_and_unicode(self):
        text = "좋아하는 메뉴는 '국수'; DROP TABLE memories; --"
        self.travel.remember(text)
        self.assertEqual(self.food.recall(), text)
        self.assertEqual(len(self.store.list_for('17')), 1)

    def test_empty_content_rejected(self):
        with self.assertRaises(ValueError):
            self.travel.remember('   ')

    def test_unknown_agent_rejected(self):
        with self.assertRaises(ValueError):
            Agent('unknown', '17', self.store)


if __name__ == '__main__':
    unittest.main(verbosity=2)
