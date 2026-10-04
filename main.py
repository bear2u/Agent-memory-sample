"""CLI: saves/reads actual SQLite data and displays model-ready messages."""
import argparse
import json
from agent import Agent, ROLES
from memory import MemoryStore


def main():
    parser = argparse.ArgumentParser(description='작은 에이전트 메모리 실습')
    parser.add_argument('--db', default='data/memory.db')
    parser.add_argument('--agent', choices=ROLES, default='travel')
    parser.add_argument('--user', default='17', help='교육용 사용자 선택. 인증 기능이 아님')
    parser.add_argument('--topic', default='food_preference')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('remember').add_argument('text')
    commands.add_parser('ask').add_argument('question')
    commands.add_parser('search').add_argument('keyword')
    for command in ('read', 'show', 'forget'):
        commands.add_parser(command)
    args = parser.parse_args()
    store = MemoryStore(args.db)
    agent = Agent(args.agent, args.user, store)
    if args.command == 'remember':
        result = {'saved': agent.remember(args.text, args.topic)}
    elif args.command == 'read':
        result = {'memory': agent.recall(args.topic)}
    elif args.command == 'ask':
        result = {'mode': 'context_only_no_llm',
                  'messages': agent.prepare(args.question, args.topic)}
        # Real LLM integration point: pass result['messages'] to your model API.
        # This project intentionally does not invent an AI-generated answer.
    elif args.command == 'search':
        result = {'matches': store.search(args.user, args.keyword)}
    elif args.command == 'show':
        result = {'rows': store.list_for(args.user)}
    else:
        result = {'deleted': agent.forget(args.topic)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
