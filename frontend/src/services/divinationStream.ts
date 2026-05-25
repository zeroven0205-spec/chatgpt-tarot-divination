import type { DivinationPayload, DivinationRequest, DivinationType } from '@/types/divination'

const API_BASE = import.meta.env.VITE_API_BASE || ''
const IS_TAURI = import.meta.env.VITE_IS_TAURI || ''

interface CustomOpenAISettings {
  enable: boolean
  baseUrl: string
  apiKey: string
  model: string
}

interface StreamDivinationOptions<T extends DivinationType> {
  promptType: T
  payload: DivinationPayload<T>
  jwt: string
  customOpenAISettings: CustomOpenAISettings
  onStart: () => void
  onChunk: (chunk: string) => void
  onDone: () => void
}

async function getErrorMessage(response: Response): Promise<string> {
  if (response.status === 429) {
    return '请求太频繁，请稍后再试'
  }

  try {
    const body = await response.clone().json()
    const detail = body.detail ?? body
    if (typeof detail === 'object' && detail !== null) {
      const detailRecord = detail as Record<string, unknown>
      if (typeof detailRecord.message === 'string') {
        return detailRecord.message
      }
    }
    if (typeof detail === 'string') {
      if (detail.includes('API KEY')) {
        return '请先配置 API KEY 和 API BASE URL'
      }
      return detail
    }
  } catch (error) {
    // If JSON parsing fails, try to read as text for error details
    try {
      const text = await response.clone().text()
      if (text.includes('<!DOCTYPE') || text.includes('<html')) {
        return '服务返回了错误页面，请检查后端服务'
      }
    } catch {
      // ignore
    }
  }

  if (response.status === 403) {
    return '当前请求未通过校验，请检查 API 配置或输入内容'
  }
  if (response.status >= 500) {
    return '服务暂时不可用，请稍后重试'
  }
  return `请求失败：${response.status} ${response.statusText}`
}

export async function streamDivination<T extends DivinationType>({
  promptType,
  payload,
  jwt,
  customOpenAISettings,
  onStart,
  onChunk,
  onDone,
}: StreamDivinationOptions<T>): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (jwt) {
    headers.Authorization = `Bearer ${jwt}`
  }

  if (customOpenAISettings.enable) {
    headers['x-api-key'] = customOpenAISettings.apiKey
    headers['x-api-url'] = customOpenAISettings.baseUrl
    headers['x-api-model'] = customOpenAISettings.model
  } else if (IS_TAURI) {
    throw new Error('请在设置中配置 API BASE URL 和 API KEY')
  }

  const requestBody = {
    ...payload,
    prompt_type: promptType,
  } as DivinationRequest<T>

  const response = await fetch(`${API_BASE}/api/divination`, {
    method: 'POST',
    body: JSON.stringify(requestBody),
    headers,
  })

  const contentType = response.headers.get('content-type') || ''

  // Check if response is SSE (text/event-stream)
  if (!contentType.startsWith('text/event-stream')) {
    throw new Error(await getErrorMessage(response))
  }

  onStart()

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('无法读取响应流')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        // Process any remaining data in buffer
        if (buffer.trim()) {
          const lines = buffer.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') {
                onDone()
                return
              }
              if (data) {
                try {
                  const parsed = JSON.parse(data)
                  if (typeof parsed === 'object' && parsed !== null && 'error' in parsed) {
                    const errorPayload = parsed as Record<string, unknown>
                    const message =
                      typeof errorPayload.message === 'string'
                        ? errorPayload.message
                        : '占卜失败，请稍后重试'
                    throw new Error(message)
                  }
                  onChunk(String(parsed))
                } catch (parseError) {
                  if (parseError instanceof Error && parseError.message.startsWith('占卜失败')) {
                    throw parseError
                  }
                  // Ignore JSON parse errors for non-data lines
                }
              }
            }
          }
        }
        onDone()
        return
      }

      buffer += decoder.decode(value, { stream: true })

      // Process complete lines
      const lines = buffer.split('\n')
      // Keep the last potentially incomplete line in buffer
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmedLine = line.trim()
        if (!trimmedLine || trimmedLine === 'data: [DONE]') {
          if (trimmedLine === 'data: [DONE]') {
            onDone()
            return
          }
          continue
        }

        if (trimmedLine.startsWith('data: ')) {
          const data = trimmedLine.slice(6)

          if (data === '[DONE]') {
            onDone()
            return
          }

          try {
            const parsed = JSON.parse(data)

            // Check for error payload
            if (typeof parsed === 'object' && parsed !== null && 'error' in parsed) {
              const errorPayload = parsed as Record<string, unknown>
              const message =
                typeof errorPayload.message === 'string'
                  ? errorPayload.message
                  : '占卜失败，请稍后重试'
              throw new Error(message)
            }

            onChunk(String(parsed))
          } catch (parseError) {
            if (parseError instanceof Error && parseError.message.startsWith('占卜失败')) {
              throw parseError
            }
            // Ignore JSON parse errors - might be partial data
          }
        }
      }
    }
  } catch (error) {
    if (error instanceof Error) {
      throw error
    }
    throw new Error('流式响应解析错误')
  } finally {
    reader.releaseLock()
  }
}
