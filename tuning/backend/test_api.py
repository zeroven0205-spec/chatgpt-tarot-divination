#!/usr/bin/env python3
"""
API 交互测试脚本

对 /api/divination 端点进行流式调用测试，用于验证：
  - 各占卜类型的实际流式输出质量
  - 不同 prompt 变体的响应差异
  - 响应延迟和完整性

用法：
    python tuning/backend/test_api.py --type dream --prompt "梦见大洪水"
    python tuning/backend/test_api.py --type tarot --prompt "感情问题"
    python tuning/backend/test_api.py --type all    # 全部类型快速扫描
    python tuning/backend/test_api.py --type dream --stream  # 显示 SSE 流内容
"""

import sys
import os
import json
import argparse
import time
from datetime import datetime

import httpx

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

ALL_TYPES = ["tarot", "dream", "birthday", "name", "new_name", "plum_flower", "fate"]

DEFAULT_PAYLOADS = {
    "tarot": {"prompt": "我最近工作不顺利，想知道接下来该如何突破", "prompt_type": "tarot"},
    "dream": {"prompt": "梦见大蛇追我", "prompt_type": "dream"},
    "birthday": {"prompt": "想了解我的人生运势", "prompt_type": "birthday", "birthday": "1990-01-01 08:00:00"},
    "name": {"prompt": "想了解这个名字的运势", "prompt_type": "name", "name": "李明"},
    "new_name": {"prompt": "想给宝宝取个好名字", "prompt_type": "new_name", "surname": "王", "sex": "male", "birthday": "2024-01-01 08:00:00"},
    "plum_flower": {"prompt": "测试梅花易数", "prompt_type": "plum_flower", "plum_flower": {"num1": 8, "num2": 3}},
    "fate": {"prompt": "我和她的姻缘如何", "prompt_type": "fate", "name1": "李明", "name2": "王芳"},
}


def test_stream(divination_type: str, payload: dict, show_stream: bool = False) -> dict:
    """发送 SSE 请求，返回测试结果"""
    url = f"{BASE_URL}/api/divination"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-api-key",
    }

    start = time.time()
    chunks = []
    chunk_count = 0
    error = None
    full_content = ""

    try:
        with httpx.stream(
            "POST", url, headers=headers, json=payload, timeout=60.0
        ) as resp:
            elapsed_ms = (time.time() - start) * 1000
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        chunk_count += 1
                        content = ""
                        if "choices" in chunk:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "") if isinstance(delta, dict) else ""
                        elif "delta" in chunk:
                            content = chunk["delta"].get("content", "") if isinstance(chunk["delta"], dict) else ""
                        chunks.append(content)
                        full_content += content
                        if show_stream:
                            print(content, end="", flush=True)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        error = str(e)

    elapsed_ms = (time.time() - start) * 1000

    result = {
        "type": divination_type,
        "payload": payload,
        "elapsed_ms": round(elapsed_ms, 1),
        "chunk_count": chunk_count,
        "content_length": len(full_content),
        "content_preview": full_content[:200],
        "error": error,
    }

    # 打印摘要
    status = "✓" if not error else "✗"
    print(f"\n{status} [{divination_type}] {result['elapsed_ms']}ms | {chunk_count} chunks | {len(full_content)} chars")
    if error:
        print(f"  ERROR: {error}")
    elif not show_stream and full_content:
        print(f"  预览: {full_content[:100].replace(chr(10), ' ')}...")

    return result


def test_all_types(show_stream: bool = False) -> list:
    """快速扫描所有类型"""
    results = []
    for dtype in ALL_TYPES:
        payload = DEFAULT_PAYLOADS.get(dtype)
        if not payload:
            continue
        print(f"\n{'='*60}")
        print(f" 测试: {dtype}")
        print(f"{'='*60}")
        if show_stream:
            print("[Stream] ", end="", flush=True)
        r = test_stream(dtype, payload, show_stream=show_stream)
        results.append(r)
    return results


def save_results(results: list, tag: str = ""):
    """保存测试结果"""
    os.makedirs("tuning/outputs", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag_str = f"_{tag}" if tag else ""
    filename = f"tuning/outputs/api_test_{ts}{tag_str}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[已保存] {filename}")


def main():
    parser = argparse.ArgumentParser(description="API 交互测试")
    parser.add_argument("--type", "-t", default=None, help=f"类型: {', '.join(ALL_TYPES)}")
    parser.add_argument("--prompt", "-p", default=None, help="自定义 prompt")
    parser.add_argument("--stream", "-s", action="store_true", help="显示 SSE 流内容")
    parser.add_argument("--save", action="store_true", help="保存结果到 outputs/")
    args = parser.parse_args()

    if args.type == "all" or args.type is None and not args.prompt:
        results = test_all_types(show_stream=args.stream)
    else:
        dtype = args.type or "dream"
        payload = DEFAULT_PAYLOADS.get(dtype, {"prompt_type": dtype}).copy()
        if args.prompt:
            payload["prompt"] = args.prompt
        payload["prompt_type"] = dtype
        print(f"\n{'='*60}")
        print(f" 测试: {dtype}")
        print(f"{'='*60}")
        if args.stream:
            print("[Stream] ", end="", flush=True)
        results = [test_stream(dtype, payload, show_stream=args.stream)]

    if args.save:
        save_results(results)

    print(f"\n{'='*60}")
    ok = sum(1 for r in results if not r.get("error"))
    print(f"完成: {ok}/{len(results)} 类型成功")
    return 0


if __name__ == "__main__":
    sys.exit(main())
