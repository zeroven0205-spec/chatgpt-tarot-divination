import { useState, useEffect } from 'react'
import { Solar } from 'lunar-javascript'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DivinationFormPage } from '@/components/DivinationFormPage'
import { useLocalStorage } from '@/hooks'
import { toast } from 'sonner'

export default function NewNamePage() {
  const [birthday, setBirthday] = useLocalStorage('birthday', '2000-08-17T00:00')
  const [sex, setSex] = useState('')
  const [surname, setSurname] = useState('')
  const [newNamePrompt, setNewNamePrompt] = useState('')
  const [lunarBirthday, setLunarBirthday] = useState('')

  const computeLunarBirthday = (birthdayStr: string) => {
    try {
      const date = new Date(birthdayStr)
      const solar = Solar.fromYmdHms(
        date.getFullYear(),
        date.getMonth() + 1,
        date.getDate(),
        date.getHours(),
        date.getMinutes(),
        date.getSeconds()
      )
      setLunarBirthday(solar.getLunar().toFullString())
    } catch (error) {
      console.error(error)
      setLunarBirthday('转换失败')
    }
  }

  useEffect(() => {
    computeLunarBirthday(birthday)
  }, [birthday])

  const handleSubmit = () => {
    if (!surname || !sex) {
      toast.error('请填写姓氏和性别')
      return null
    }

    const date = new Date(birthday)
    const formattedBirthday = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0') + ' ' +
      String(date.getHours()).padStart(2, '0') + ':' +
      String(date.getMinutes()).padStart(2, '0') + ':' +
      String(date.getSeconds()).padStart(2, '0')

    return {
      prompt: `${surname} ${sex} ${formattedBirthday}`,
      birthday: formattedBirthday,
      new_name: {
        surname,
        sex,
        birthday: formattedBirthday,
        new_name_prompt: newNamePrompt,
      },
    }
  }

  return (
    <DivinationFormPage type="new_name" onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <Label>姓氏</Label>
          <Input
            value={surname}
            onChange={(e) => setSurname(e.target.value)}
            placeholder="请输入姓氏"
            maxLength={2}
            className="mt-2"
          />
        </div>
        <div>
          <Label>性别</Label>
          <Select value={sex} onValueChange={setSex}>
            <SelectTrigger className="mt-2">
              <SelectValue placeholder="请选择性别" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="男">男</SelectItem>
              <SelectItem value="女">女</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="block mb-2">生日</Label>
          <Input
            type="datetime-local"
            value={birthday}
            onChange={(e) => setBirthday(e.target.value)}
            className="w-auto inline-block"
          />
        </div>
        <div>
          <Label>附加要求</Label>
          <Input
            value={newNamePrompt}
            onChange={(e) => setNewNamePrompt(e.target.value)}
            maxLength={20}
            placeholder="例如：希望名字带水"
            className="mt-2"
          />
        </div>
        <p className="text-sm text-muted-foreground">农历: {lunarBirthday}</p>
      </div>
    </DivinationFormPage>
  )
}
