import { Textarea } from '@/components/ui/textarea'
import { DivinationFormPage } from '@/components/DivinationFormPage'
import { useLocalStorage } from '@/hooks'

export default function TarotPage() {
  const [prompt, setPrompt] = useLocalStorage('prompt', '')

  return (
    <DivinationFormPage
      type="tarot"
      onSubmit={() => ({
        prompt: prompt || '我的财务状况如何',
      })}
    >
      <div className="space-y-4">
        <Textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="我的财务状况如何"
          maxLength={40}
          rows={3}
          className="resize-none w-full"
        />
        <p className="text-xs text-muted-foreground">
          请输入您想要占卜的问题（最多40字）
        </p>
      </div>
    </DivinationFormPage>
  )
}
