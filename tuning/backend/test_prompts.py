#!/usr/bin/env python3
"""
Prompt 模板测试脚本

直接调用 DivinationFactory.build_prompt() 查看各类型实际输出的 prompt，
用于快速迭代优化 prompt 模板，无需启动服务。

用法：
    python tuning/backend/test_prompts.py
    python tuning/backend/test_prompts.py --type tarot
    python tuning/backend/test_prompts.py --type all --verbose
"""

import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.divination.base import DivinationFactory, MetaDivination
from src.divination.prompt_registry import get_evaluation_fixtures, get_prompt_variant
from src.models import DivinationBody

ALL_TYPES = list(MetaDivination.divination_map.keys())
DEFAULT_INPUTS = {
    dtype: fixtures[0]
    for dtype, fixtures in get_evaluation_fixtures().items()
    if fixtures
}


def build_body(dtype: str, params: dict) -> DivinationBody:
    kwargs = {"prompt": params["prompt"], "prompt_type": dtype}
    extra = {k: v for k, v in params.items() if k != "prompt"}
    kwargs.update(extra)
    return DivinationBody(**kwargs)


def test_type(dtype: str, custom_input: dict = None, verbose: bool = False):
    """测试单个类型"""
    params = custom_input or DEFAULT_INPUTS.get(dtype, {"prompt": "通用测试"})
    factory = DivinationFactory.get(dtype)

    if factory is None:
        print(f"[SKIP] 未注册类型: {dtype}，可用: {ALL_TYPES}")
        return None

    try:
        body = build_body(dtype, params)
        user_prompt, system_prompt = factory.build_prompt(body)
    except Exception as e:
        print(f"[ERROR] {dtype}: {e}")
        return None

    print(f"\n{'─'*60}")
    variant = get_prompt_variant(dtype)
    print(f"  {dtype} | variant={variant.id} | temp={variant.temperature} | max_tokens={variant.max_tokens}")
    print(f"{'─'*60}")
    print(f"\n[ System ]")
    print(system_prompt or "(空)")
    print(f"\n[ User ]")
    print(user_prompt)

    if verbose:
        print(f"\n[ Input params ] {params}")

    return {"type": dtype, "system": system_prompt, "user": user_prompt, "input": params}


def main():
    parser = argparse.ArgumentParser(description="Prompt 模板测试")
    parser.add_argument("--type", "-t", default=None,
                        help=f"类型: {', '.join(ALL_TYPES)}, 默认全部")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细模式")
    args = parser.parse_args()

    types = [args.type] if args.type else ALL_TYPES

    results = []
    for dtype in types:
        r = test_type(dtype, verbose=args.verbose)
        if r:
            results.append(r)

    print(f"\n\n{'='*60}")
    print(f"测试完成: {len(results)}/{len(types)} 类型通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
