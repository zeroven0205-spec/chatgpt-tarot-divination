import { getDivinationOption } from '@/config/constants'
import { saveHistory } from '@/utils/divinationHistory'
import type { DivinationPayload, DivinationType } from '@/types/divination'

export function saveDivinationHistory<T extends DivinationType>(
  promptType: T,
  payload: DivinationPayload<T>,
  result: string
) {
  if (!result) {
    return
  }

  const config = getDivinationOption(promptType)
  if (!config) {
    return
  }

  saveHistory({
    type: promptType,
    title: config.title,
    prompt: payload.prompt,
    result,
  })
}
