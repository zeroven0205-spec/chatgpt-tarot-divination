import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { DivinationFormPage } from '@/components/DivinationFormPage'
import { useLocalStorage } from '@/hooks'

export default function FatePage() {
  const [fate, setFate] = useLocalStorage('fate_body', {
    name1: '',
    name2: '',
  })

  const handleSubmit = () => {
    return {
      prompt: `${fate.name1} ${fate.name2}`,
      fate,
    }
  }

  return (
    <DivinationFormPage type="fate" onSubmit={handleSubmit} submitLabel="一键预测">
      <div className="space-y-4">
        <h4 className="font-medium">缘分是天定的，幸福是自己的。</h4>
        <p className="text-sm text-muted-foreground">
          想知道你和 ta 有没有缘分呢，编辑"姓名1" "姓名2"，然后点击"一键预测"。
        </p>
        <p className="text-sm text-muted-foreground">
          如郭靖 黄蓉，然后点击一键预测。 就能查看你和 ta 的缘分了。
        </p>
        <div>
          <Label>姓名1</Label>
          <Input
            value={fate.name1}
            onChange={(e) => setFate({ ...fate, name1: e.target.value })}
            maxLength={40}
            className="mt-2"
          />
        </div>
        <div>
          <Label>姓名2</Label>
          <Input
            value={fate.name2}
            onChange={(e) => setFate({ ...fate, name2: e.target.value })}
            maxLength={40}
            className="mt-2"
          />
        </div>
        <div className="text-center text-sm">
          <a
            href="https://github.com/alongLFB/alonglfb.github.io/blob/master/images/wechatpay.png"
            className="text-primary hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            请作者喝杯咖啡
          </a>{' '}
          - 🤗 Along Li
        </div>
      </div>
    </DivinationFormPage>
  )
}
