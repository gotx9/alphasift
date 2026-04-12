# -*- coding: utf-8 -*-
"""CLI entry point."""

import argparse
import json
import logging
import sys
from dataclasses import asdict

from alphasift.config import Config
from alphasift.pipeline import screen
from alphasift.strategy import list_strategies


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(prog="alphasift", description="自动选股 Skill")
    sub = parser.add_subparsers(dest="command")

    # screen
    sp = sub.add_parser("screen", help="执行选股")
    sp.add_argument("strategy", help="策略名称")
    sp.add_argument("--market", default="cn")
    sp.add_argument("--max-output", type=int, default=None)
    sp.add_argument("--no-llm", action="store_true", help="不使用 LLM 排序")
    sp.add_argument("--deep-analysis", action="store_true", help="调用 DSA 做 L3 深度分析")
    sp.add_argument(
        "--deep-analysis-max-picks",
        type=int,
        default=None,
        help="最多对前 N 只候选调用 DSA（默认使用环境变量或 3）",
    )

    # strategies
    sub.add_parser("strategies", help="列出可用策略")

    args = parser.parse_args()

    if args.command == "screen":
        config = Config.from_env()
        result = screen(
            args.strategy,
            market=args.market,
            max_output=args.max_output,
            use_llm=not args.no_llm,
            deep_analysis=args.deep_analysis,
            deep_analysis_max_picks=args.deep_analysis_max_picks,
            config=config,
        )
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))

    elif args.command == "strategies":
        for s in list_strategies():
            print(f"  {s.name:<25} {s.display_name:<10} [{s.category}] {s.description}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
