#!/bin/bash
#
# 快速运行所有测试
# 依赖：后端服务运行在 localhost:8000
#
# 用法：
#   bash tuning/scripts/run_all.sh          # 运行全部
#   bash tuning/scripts/run_all.sh --api   # 仅 API 测试
#   bash tuning/scripts/run_all.sh --prompt # 仅 Prompt 测试

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_DIR"

echo "============================================"
echo "  Tarot Divination Tuning - 全量测试"
echo "============================================"

# 检查后端是否运行
if ! curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "[WARN] 后端服务未运行在 localhost:8000"
    echo "请先启动: python main.py"
    exit 1
fi
echo "[OK] 后端服务正常"

# 检查 venv
if [ -d "venv" ]; then
    VENV_PY="venv/bin/python"
else
    VENV_PY="python3"
fi

MODE="${1:-all}"

run_prompt_tests() {
    echo ""
    echo ">>> Prompt 模板测试"
    echo "--------------------------------------------"
    $VENV_PY tuning/backend/test_prompts.py
}

run_api_tests() {
    echo ""
    echo ">>> API 流式响应测试"
    echo "--------------------------------------------"
    $VENV_PY tuning/backend/test_api.py --save
}

run_factory_tests() {
    echo ""
    echo ">>> Factory Prompt 构建测试"
    echo "--------------------------------------------"
    $VENV_PY tuning/runner.py --type all --save
}

case "$MODE" in
    --api)
        run_api_tests
        ;;
    --prompt)
        run_prompt_tests
        ;;
    --factory)
        run_factory_tests
        ;;
    *)
        run_prompt_tests
        run_api_tests
        run_factory_tests
        ;;
esac

echo ""
echo "============================================"
echo "  测试完成，结果保存在 tuning/outputs/"
echo "============================================"
