import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { DivinationFormPage } from '@/components/DivinationFormPage'
import { useLocalStorage } from '@/hooks'

export default function PlumFlowerPage() {
  const [plumFlower, setPlumFlower] = useLocalStorage('plum_flower', {
    num1: 0,
    num2: 0,
  })

  const handleSubmit = () => {
    return {
      prompt: `${plumFlower.num1} ${plumFlower.num2}`,
      plum_flower: plumFlower,
    }
  }

  return (
    <DivinationFormPage type="plum_flower" onSubmit={handleSubmit}>
      <div className="space-y-4">
        <h4 className="font-medium">请随机输入两个 0-1000 的数字</h4>
        <div>
          <Label>数字一</Label>
          <Input
            type="number"
            min={0}
            max={1000}
            value={plumFlower.num1}
            onChange={(e) =>
              setPlumFlower({ ...plumFlower, num1: parseInt(e.target.value) || 0 })
            }
            className="mt-2"
          />
        </div>
        <div>
          <Label>数字二</Label>
          <Input
            type="number"
            min={0}
            max={1000}
            value={plumFlower.num2}
            onChange={(e) =>
              setPlumFlower({ ...plumFlower, num2: parseInt(e.target.value) || 0 })
            }
            className="mt-2"
          />
        </div>
      </div>
    </DivinationFormPage>
  )
}
