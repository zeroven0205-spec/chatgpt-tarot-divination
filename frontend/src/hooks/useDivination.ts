import { useMemo, useState } from 'react'
import MarkdownIt from 'markdown-it'
import { useGlobalState } from '@/store'
import { streamDivination } from '@/services/divinationStream'
import { saveDivinationHistory } from '@/hooks/useDivinationHistory'
import type { DivinationPayload, DivinationType } from '@/types/divination'

const md = new MarkdownIt()

export function useDivination<T extends DivinationType>(promptType: T) {
  const { jwt, customOpenAISettings } = useGlobalState()
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultLoading, setResultLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [showDrawer, setShowDrawer] = useState(false)

  const resultHtml = useMemo(() => md.render(result), [result])

  const onSubmit = async (payload: DivinationPayload<T>) => {
    setLoading(true)
    setResultLoading(true)
    setStreaming(false)
    setResult('')
    setShowDrawer(true)

    let rawResult = ''
    let firstChunk = true

    try {
      await streamDivination({
        promptType,
        payload,
        jwt,
        customOpenAISettings,
        onStart() {
          setStreaming(true)
        },
        onChunk(chunk) {
          rawResult += chunk
          setResult(rawResult)

          if (firstChunk) {
            firstChunk = false
            setResultLoading(false)
            setLoading(false)
          }
        },
        onDone() {
          setStreaming(false)
        },
      })

      saveDivinationHistory(promptType, payload, rawResult)
    } catch (error) {
      const message = error instanceof Error ? error.message : '占卜失败'
      console.error(error)
      setResult(message)
      setStreaming(false)
    } finally {
      setLoading(false)
      setResultLoading(false)
      setStreaming(false)
    }
  }

  return {
    result,
    resultHtml,
    loading,
    resultLoading,
    streaming,
    showDrawer,
    setShowDrawer,
    onSubmit,
  }
}
