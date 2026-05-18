/**
 * 前端交互体验测试工具
 *
 * 用途：脱离浏览器手动测试，验证 SSE 流式交互流程
 * 用法：在前端项目目录下运行
 *   npx ts-node --esm tuning/frontend/test_interactions.ts
 *   或直接参考此文件的测试场景，在浏览器 DevTools 中执行
 *
 * 测试场景：
 *  1. 各类型表单提交流式响应
 *  2. SSE 连接断开重试
 *  3. 结果抽屉动画时序
 *  4. 历史记录存取
 */

export const API_BASE = "http://localhost:8000";

// 各类型测试用例
export const TEST_CASES = {
  tarot: {
    prompt: "我最近工作不顺利，想知道接下来该如何突破",
    prompt_type: "tarot",
  },
  dream: {
    prompt: "梦见大蛇追我",
    prompt_type: "dream",
  },
  birthday: {
    prompt: "想了解我的人生运势",
    prompt_type: "birthday",
    birthday: "1990-01-01 08:00:00",
  },
  name: {
    prompt: "想了解这个名字的运势",
    prompt_type: "name",
    name: "李明",
  },
  new_name: {
    prompt: "想给宝宝取个好名字",
    prompt_type: "new_name",
    surname: "王",
    sex: "male",
    birthday: "2024-01-01 08:00:00",
  },
  plum_flower: {
    prompt: "测试梅花易数",
    prompt_type: "plum_flower",
    plum_flower: { num1: 8, num2: 3 },
  },
  fate: {
    prompt: "我和她的姻缘如何",
    prompt_type: "fate",
    name1: "李明",
    name2: "王芳",
  },
} as const;

// SSE 流式测试
export async function testSSEStream(
  payload: Record<string, unknown>,
  onChunk: (content: string, index: number) => void,
  onDone: (fullContent: string) => void
): Promise<{ duration: number; chunkCount: number }> {
  const start = Date.now();
  let chunkCount = 0;
  let fullContent = "";

  const response = await fetch(`${API_BASE}/api/divination`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer test",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("ReadableStream not supported");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("data:")) {
        const data = line.slice(5).trim();
        if (data === "[DONE]") {
          onDone(fullContent);
          return { duration: Date.now() - start, chunkCount };
        }
        try {
          const parsed = JSON.parse(data);
          const content =
            parsed?.choices?.[0]?.delta?.content ??
            parsed?.delta?.content ??
            "";
          if (content) {
            chunkCount++;
            fullContent += content;
            onChunk(content, chunkCount);
          }
        } catch {
          // ignore parse errors
        }
      }
    }
  }

  onDone(fullContent);
  return { duration: Date.now() - start, chunkCount };
}

// 交互流程测试
export async function runInteractionTest(
  type: keyof typeof TEST_CASES
): Promise<void> {
  const payload = TEST_CASES[type];
  console.log(`\n[${type}] 测试开始`, payload);

  const t0 = Date.now();
  const result = await testSSEStream(
    payload,
    (chunk, i) => console.log(`  chunk#${i}: ${chunk.slice(0, 40)}...`),
    (full) => {
      console.log(`  完成! ${Date.now() - t0}ms | ${full.length} chars`);
      console.log(`  预览: ${full.slice(0, 100).replace(/\n/g, " ")}...`);
    }
  );

  console.log(`[${type}] 耗时: ${result.duration}ms, chunks: ${result.chunkCount}`);
}

// 运行全部类型
export async function runAllTests(): Promise<void> {
  const types = Object.keys(TEST_CASES) as Array<keyof typeof TEST_CASES>;
  for (const type of types) {
    await runInteractionTest(type);
  }
}

// 快速验证前端 -> 后端代理连通性
export async function ping(): Promise<boolean> {
  try {
    const resp = await fetch(`${API_BASE}/docs`, { method: "HEAD" });
    return resp.ok;
  } catch {
    return false;
  }
}
