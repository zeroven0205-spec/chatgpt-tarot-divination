#!/usr/bin/env python3
"""
Tuning Runner - 占卜项目交互体验调优主脚本

功能：
  - 直接调用 DivinationFactory 测试所有 7 种占卜类型的 prompt 构建
  - 调用 API 并对比不同 prompt 的流式输出质量
  - 保存每次测试结果到 outputs/ 目录

用法：
    python tuning/runner.py                    # 交互式选择类型测试
    python tuning/runner.py --type tarot       # 指定类型
    python tuning/runner.py --type all         # 运行全部类型
    python tuning/runner.py --type tarot --compare  # 对比模式
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.divination.base import DivinationFactory, MetaDivination
from src.models import DivinationBody


DIVINATION_TYPES = list(MetaDivination.divination_map.keys())
DEFAULT_TEST_CASES = {
    "tarot": {"prompt": "我最近工作不顺利，想知道接下来该如何突破"},
    "dream": {"prompt": "梦见大蛇追我"},
    "birthday": {"prompt": "想了解我的人生运势", "birthday": "1990-01-01 08:00:00"},
    "name": {"prompt": "想了解这个名字的运势", "name": "李明"},
    "new_name": {"prompt": "想给宝宝取个好名字", "surname": "王", "sex": "male", "birthday": "2024-01-01 08:00:00"},
    "plum_flower": {"prompt": "测试梅花易数", "plum_flower": {"num1": 8, "num2": 3}},
    "fate": {"prompt": "我和她的姻缘如何", "name1": "李明", "name2": "王芳"},
}


def build_body(divination_type: str, params: dict) -> DivinationBody:
    """根据类型构造 DivinationBody"""
    base = {"prompt": params.get("prompt", "测试")}
    extra = {k: v for k, v in params.items() if k != "prompt"}
    return DivinationBody(**base, **{"prompt_type": divination_type}, **extra)


def test_prompt_build(divination_type: str, params: dict) -> dict:
    """测试 prompt 构建，返回构建结果"""
    factory = DivinationFactory.get(divination_type)
    if factory is None:
        return {"error": f"未找到类型: {divination_type}, 可用: {DIVINATION_TYPES}"}

    try:
        body = build_body(divination_type, params)
        user_prompt, system_prompt = factory.build_prompt(body)
        return {
            "type": divination_type,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "params": params,
            "factory": factory.__class__.__name__,
        }
    except Exception as e:
        return {"error": str(e), "type": divination_type, "params": params}


def print_prompt_result(result: dict, verbose: bool = False):
    """打印 prompt 测试结果"""
    if "error" in result:
        print(f"[ERROR] {result['type']}: {result['error']}")
        return

    print(f"\n{'='*60}")
    print(f"类型: {result['type']} | Factory: {result['factory']}")
    print(f"{'='*60}")
    print(f"\n[System Prompt]")
    print(result["system_prompt"])
    print(f"\n[User Prompt]")
    print(result["user_prompt"])
    if verbose:
        print(f"\n[Params] {result['params']}")


def save_result(result: dict, tag: str = ""):
    """保存结果到 outputs/ 目录"""
    os.makedirs("tuning/outputs", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag_str = f"_{tag}" if tag else ""
    filename = f"tuning/outputs/{result.get('type', 'unknown')}_{ts}{tag_str}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[已保存] {filename}")
    return filename


def interactive_menu():
    """交互式菜单"""
    print("\n可用占卜类型:")
    for i, t in enumerate(DIVINATION_TYPES, 1):
        print(f"  {i}. {t}")
    print(f"  0. 全部类型")
    print(f"  q. 退出")

    try:
        choice = input("\n请选择 (编号): ").strip()
    except EOFError:
        choice = "q"

    if choice == "q":
        return None
    if choice == "0":
        return "all"
    try:
        idx = int(choice) - 1
        return DIVINATION_TYPES[idx]
    except:
        return None


def run_all_types():
    """运行所有类型"""
    results = []
    for dtype in DIVINATION_TYPES:
        params = DEFAULT_TEST_CASES.get(dtype, {"prompt": "测试"})
        print(f"\n>>> 测试 {dtype}...")
        result = test_prompt_build(dtype, params)
        print_prompt_result(result)
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description="占卜项目 Tuning Runner")
    parser.add_argument("--type", "-t", type=str, default=None,
                        help=f"占卜类型: {', '.join(DIVINATION_TYPES)}, all, 或留空交互选择")
    parser.add_argument("--compare", action="store_true", help="对比模式")
    parser.add_argument("--save", "-s", action="store_true", help="保存结果到 outputs/")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    args = parser.parse_args()

    divination_type = args.type

    if divination_type is None:
        divination_type = interactive_menu()
        if divination_type is None:
            print("无效选择，退出")
            return

    if divination_type == "all":
        results = run_all_types()
    else:
        params = DEFAULT_TEST_CASES.get(divination_type, {"prompt": "测试"})
        result = test_prompt_build(divination_type, params)
        print_prompt_result(result, verbose=args.verbose)
        results = [result]

    if args.save:
        for r in results:
            if "error" not in r:
                save_result(r)


if __name__ == "__main__":
    main()
