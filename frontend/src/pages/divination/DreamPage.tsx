import { Textarea } from '@/components/ui/textarea'
import { DivinationFormPage } from '@/components/DivinationFormPage'
import { useLocalStorage } from '@/hooks'

export default function DreamPage() {
  const [prompt, setPrompt] = useLocalStorage('dream_prompt', '')

  return (
    <DivinationFormPage
      type="dream"
      onSubmit={() => ({
        prompt,
      })}
    >
      <div>
        <Textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="请输入你的梦境"
          maxLength={40}
          rows={3}
          className="resize-none"
        />
        <p className="text-xs text-muted-foreground mt-2">
          请详细描述您的梦境（最多40字）
        </p>
      </div>
    </DivinationFormPage>
  )
}
