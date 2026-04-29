#!/usr/bin/env python3
"""
MiniMax M2.7 API 兼容性验证脚本
阶段一：接口验证

执行方式：
    python test_minimax_stream.py

前提：
    1. 设置环境变量 MINIMAX_API_KEY 和 MINIMAX_BASE_URL
       或直接修改下方 MINIMAX_API_KEY / MINIMAX_BASE_URL 常量
    2. pip install httpx requests
"""

import os
import json
import sys

# ===== 配置区 - 请填写你的 MiniMax API 信息 =====
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7")
# ================================================

def test_basic_chat():
    """1.1 验证基本 Chat Completions 端点"""
    print("\n" + "=" * 60)
    print("测试 1.1：基本 Chat Completions 端点")
    print("=" * 60)

    if not MINIMAX_API_KEY:
        print("[SKIP] MINIMAX_API_KEY 未设置，请先配置")
        return False

    try:
        import httpx

        with httpx.stream(
            "POST",
            f"{MINIMAX_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MINIMAX_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个占卜师，用一句话回复"},
                    {"role": "user", "content": "塔罗牌是什么"}
                ],
                "max_tokens": 50,
                "temperature": 0.9,
            },
            timeout=30.0
        ) as resp:
            print(f"HTTP Status: {resp.status_code}")
            print(f"Headers: {dict(resp.headers)}")

            if resp.status_code != 200:
                print(f"[WARN] 状态码非 200: {resp.status_code}")
                try:
                    error_body = resp.read().decode("utf-8")
                    print(f"响应体: {error_body[:500]}")
                except:
                    pass
                return False

            body = resp.read().decode("utf-8")
            data = json.loads(body)
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"[OK] 响应内容: {content}")
            return True

    except ImportError:
        print("[ERROR] httpx 未安装，请运行: pip install httpx")
        return False
    except Exception as e:
        print(f"[ERROR] 请求失败: {type(e).__name__}: {e}")
        return False


def test_streaming():
    """1.2 验证流式响应格式"""
    print("\n" + "=" * 60)
    print("测试 1.2：流式响应格式 (stream=True)")
    print("=" * 60)

    if not MINIMAX_API_KEY:
        print("[SKIP] MINIMAX_API_KEY 未设置")
        return False

    try:
        import httpx

        chunk_count = 0
        first_chunk = None

        with httpx.stream(
            "POST",
            f"{MINIMAX_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MINIMAX_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个占卜师"},
                    {"role": "user", "content": "简述塔罗牌的历史，不超过50字"}
                ],
                "max_tokens": 100,
                "temperature": 0.9,
                "stream": True
            },
            timeout=30.0
        ) as resp:
            print(f"HTTP Status: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type', 'unknown')}")

            if resp.status_code != 200:
                print(f"[WARN] 状态码非 200: {resp.status_code}")
                return False

            for line in resp.iter_lines():
                if not line:
                    continue

                # SSE 格式检查
                if line.startswith("data:"):
                    data_content = line[5:].strip()
                    if data_content == "[DONE]":
                        print(f"[SSE] 流结束标识: data: [DONE]")
                        continue

                    try:
                        parsed = json.loads(data_content)
                        chunk_count += 1

                        if chunk_count == 1:
                            first_chunk = parsed
                            print(f"[SSE] 首个 chunk 结构: {json.dumps(parsed, ensure_ascii=False)[:200]}")

                        # 检查 OpenAI 兼容格式
                        delta = None
                        if isinstance(parsed, dict):
                            # OpenAI 标准格式
                            if "choices" in parsed:
                                delta = parsed["choices"][0].get("delta", {}).get("content")
                            # MiniMax 可能的不同格式
                            elif "delta" in parsed:
                                delta = parsed["delta"].get("content") if isinstance(parsed["delta"], dict) else parsed["delta"]

                        if delta:
                            print(f"[SSE] chunk #{chunk_count}: {delta[:30]}...")
                            break  # 已确认能拿到内容，停止打印

                    except json.JSONDecodeError:
                        print(f"[SSE] 无法解析的 chunk: {data_content[:100]}")
                        continue

            print(f"[OK] 共收到 {chunk_count} 个 SSE chunk")
            if first_chunk:
                print(f"[STRUCTURE] 首个 chunk 完整内容: {json.dumps(first_chunk, ensure_ascii=False)[:300]}")
            return chunk_count > 0

    except ImportError:
        print("[ERROR] httpx 未安装")
        return False
    except Exception as e:
        print(f"[ERROR] 流式测试失败: {type(e).__name__}: {e}")
        return False


def test_params():
    """1.3 验证参数支持范围"""
    print("\n" + "=" * 60)
    print("测试 1.3：参数支持范围")
    print("=" * 60)

    if not MINIMAX_API_KEY:
        print("[SKIP] MINIMAX_API_KEY 未设置")
        return False

    try:
        import httpx

        test_cases = [
            {"name": "max_tokens=1000", "params": {"max_tokens": 1000}},
            {"name": "max_tokens=500", "params": {"max_tokens": 500}},
            {"name": "temperature=0.9", "params": {"temperature": 0.9}},
            {"name": "temperature=0.0", "params": {"temperature": 0.0}},
            {"name": "temperature=1.0", "params": {"temperature": 1.0}},
            {"name": "top_p=1.0", "params": {"top_p": 1.0}},
            {"name": "top_p=0.9", "params": {"top_p": 0.9}},
        ]

        results = []
        for tc in test_cases:
            try:
                with httpx.stream(
                    "POST",
                    f"{MINIMAX_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MINIMAX_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": MINIMAX_MODEL,
                        "messages": [
                            {"role": "user", "content": "hi"}
                        ],
                        "max_tokens": 10,
                        "stream": False,
                        **tc["params"]
                    },
                    timeout=15.0
                ) as resp:
                    if resp.status_code == 200:
                        print(f"[OK] {tc['name']}")
                        results.append((tc["name"], True, ""))
                    else:
                        err = resp.read().decode("utf-8")[:100]
                        print(f"[FAIL] {tc['name']} -> {resp.status_code}: {err}")
                        results.append((tc["name"], False, err))
            except Exception as e:
                print(f"[ERROR] {tc['name']} -> {type(e).__name__}: {e}")
                results.append((tc["name"], False, str(e)))

        print("\n--- 参数支持汇总 ---")
        for name, ok, err in results:
            status = "✓ 支持" if ok else "✗ 不支持"
            print(f"  {status}  {name}{f' ({err})' if err else ''}")

        return all(ok for _, ok, _ in results)

    except ImportError:
        print("[ERROR] httpx 未安装")
        return False


def main():
    print("MiniMax M2.7 API 兼容性验证脚本")
    print(f"API Base: {MINIMAX_BASE_URL}")
    print(f"Model: {MINIMAX_MODEL}")

    if not MINIMAX_API_KEY:
        print("\n[ERROR] 请设置环境变量 MINIMAX_API_KEY 或修改脚本中的 MINIMAX_API_KEY")
        print("  export MINIMAX_API_KEY=your_key_here")
        print("  export MINIMAX_BASE_URL=https://api.minimax.chat/v1")
        print("  python test_minimax_stream.py")
        sys.exit(1)

    results = {}

    results["1.1_basic_chat"] = test_basic_chat()
    results["1.2_streaming"] = test_streaming()
    results["1.3_params"] = test_params()

    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    for name, ok in results.items():
        status = "✓ 通过" if ok else "✗ 失败"
        print(f"  {status}  {name}")

    all_passed = all(results.values())
    print(f"\n结论: {'全部通过，可以进入阶段二' if all_passed else '存在失败项，请先解决接口兼容性问题'}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
