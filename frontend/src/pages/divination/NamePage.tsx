import { Input } from '@/components/ui/input'
import { DivinationFormPage } from '@/components/DivinationFormPage'
import { useLocalStorage } from '@/hooks'

export default function NamePage() {
  const [prompt, setPrompt] = useLocalStorage('name_prompt', '')

  return (
    <DivinationFormPage
      type="name"
      onSubmit={() => ({
        prompt,
      })}
    >
      <div>
        <Input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="请输入姓名"
          maxLength={10}
        />
        <p className="text-xs text-muted-foreground mt-2">
          请输入完整姓名（最多10字）
        </p>
      </div>
    </DivinationFormPage>
  )
}
