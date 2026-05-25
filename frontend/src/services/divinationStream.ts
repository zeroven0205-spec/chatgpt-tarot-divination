import { fetchEventSource, EventStreamContentType } from '@microsoft/fetch-event-source'
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
    console.error(error)
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

  await fetchEventSource(`${API_BASE}/api/divination`, {
    method: 'POST',
    body: JSON.stringify(requestBody),
    headers,
    async onopen(response) {
      if (response.ok && response.headers.get('content-type') === EventStreamContentType) {
        onStart()
        return
      }
      throw new Error(await getErrorMessage(response))
    },
    onmessage(msg) {
      if (msg.event === 'FatalError') {
        throw new Error(msg.data)
      }
      if (!msg.data) {
        return
      }
      if (msg.data === '[DONE]') {
        onDone()
        return
      }

      let parsedContent: unknown
      try {
        parsedContent = JSON.parse(msg.data)
      } catch (error) {
        console.error(error)
        return
      }

      if (
        typeof parsedContent === 'object' &&
        parsedContent !== null &&
        'error' in parsedContent
      ) {
        const errorPayload = parsedContent as Record<string, unknown>
        const message =
          typeof errorPayload.message === 'string'
            ? errorPayload.message
            : '占卜失败，请稍后重试'
        throw new Error(message)
      }

      onChunk(String(parsedContent))
    },
    onclose() {
      onDone()
    },
    onerror(error) {
      const message = error instanceof Error ? error.message : '网络连接异常，请稍后重试'
      throw new Error(message)
    },
  })
}
