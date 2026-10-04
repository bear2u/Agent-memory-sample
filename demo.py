"""Every step starts a NEW Python process against the same SQLite file."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def run(db, agent, user, *args):
    command = [sys.executable, str(ROOT / 'main.py'), '--db', str(db),
               '--agent', agent, '--user', user, *args]
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    return json.loads(subprocess.check_output(command, encoding='utf-8', env=env))


def main():
    events = []
    # Fresh disposable database: existing learner data is never reset/deleted.
    with tempfile.TemporaryDirectory(prefix='agent-memory-demo-') as folder:
        db = Path(folder) / 'memory.db'
        steps = [
            ('1. 기억 없는 질문', 'food', '17', 'ask', '오늘 저녁 뭐 먹을까?'),
            ('2. 길잡이가 저장', 'travel', '17', 'remember', '매운 음식을 못 먹음'),
            ('3. 저장된 실제 행', 'travel', '17', 'show'),
            ('4. 새 프로세스의 밥친구가 읽음', 'food', '17', 'read'),
            ('5. 질문에 메모를 붙임', 'food', '17', 'ask', '오늘 저녁 뭐 먹을까?'),
            ('6. 단순 문자열 검색', 'food', '17', 'search', '매운'),
            ('7. 다른 사용자는 분리', 'food', '99', 'read'),
            ('8. 현재 취향 수정', 'travel', '17', 'remember', '약간 매운 음식은 괜찮고, 아주 매운 음식은 피함'),
            ('9. 밥친구가 수정된 메모 읽음', 'food', '17', 'read'),
            ('10. 기억 삭제', 'travel', '17', 'forget'),
            ('11. 새 조회에서 사라짐', 'food', '17', 'read'),
        ]
        for title, agent, user, *args in steps:
            event = {'step': title, 'agent': agent, 'user': user,
                     'command': args, 'output': run(db, agent, user, *args)}
            events.append(event)
    print(json.dumps(events, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
