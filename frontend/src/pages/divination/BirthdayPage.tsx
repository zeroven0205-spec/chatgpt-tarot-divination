import { useState, useEffect } from 'react'
import { Solar } from 'lunar-javascript'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { DivinationFormPage } from '@/components/DivinationFormPage'
import { useLocalStorage } from '@/hooks'

export default function BirthdayPage() {
  const [birthday, setBirthday] = useLocalStorage('birthday', '2000-08-17T00:00')
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
    const date = new Date(birthday)
    const formattedBirthday = date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0') + ' ' +
      String(date.getHours()).padStart(2, '0') + ':' +
      String(date.getMinutes()).padStart(2, '0') + ':' +
      String(date.getSeconds()).padStart(2, '0')

    return {
      prompt: formattedBirthday,
      birthday: formattedBirthday,
    }
  }

  return (
    <DivinationFormPage type="birthday" onSubmit={handleSubmit}>
      <div className="space-y-4">
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
          <Label>农历</Label>
          <p className="text-sm mt-2 text-foreground/80">{lunarBirthday}</p>
        </div>
      </div>
    </DivinationFormPage>
  )
}
