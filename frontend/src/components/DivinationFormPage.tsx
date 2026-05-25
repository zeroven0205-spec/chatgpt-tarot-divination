import { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { DivinationCardHeader } from '@/components/DivinationCardHeader'
import { ResultDrawer } from '@/components/ResultDrawer'
import { useDivination } from '@/hooks/useDivination'
import { getDivinationOption } from '@/config/constants'
import { Sparkles, Eye, Loader2 } from 'lucide-react'
import type { DivinationPayload, DivinationType } from '@/types/divination'

interface DivinationFormPageProps<T extends DivinationType> {
  type: T
  children: ReactNode
  onSubmit: () => DivinationPayload<T> | null | undefined
  submitLabel?: string
  loadingLabel?: string
  contentClassName?: string
}

export function DivinationFormPage<T extends DivinationType>({
  type,
  children,
  onSubmit,
  submitLabel = '开始占卜',
  loadingLabel = '占卜中',
  contentClassName = 'w-full max-w-2xl mx-auto',
}: DivinationFormPageProps<T>) {
  const config = getDivinationOption(type)!
  const {
    result,
    resultHtml,
    loading,
    resultLoading,
    streaming,
    showDrawer,
    setShowDrawer,
    onSubmit: submitDivination,
  } = useDivination(type)

  const handleSubmit = () => {
    const payload = onSubmit()
    if (!payload) {
      return
    }
    submitDivination(payload)
  }

  return (
    <DivinationCardHeader
      title={config.title}
      description={config.description}
      icon={config.icon}
      divinationType={type}
    >
      <div className={contentClassName}>
        {children}

        <div className="flex gap-2 md:gap-3 justify-center pt-4 md:pt-6">
          <Button
            onClick={() => setShowDrawer(!showDrawer)}
            variant="outline"
            className="gap-2 flex-1 md:flex-initial md:min-w-[140px]"
            disabled={!result}
          >
            <Eye className="h-4 w-4" />
            查看结果
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="gap-2 flex-1 md:flex-initial md:min-w-[140px] bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {loadingLabel}
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                {submitLabel}
              </>
            )}
          </Button>
        </div>
      </div>

      <ResultDrawer
        show={showDrawer}
        onClose={() => setShowDrawer(false)}
        result={resultHtml}
        rawResult={result}
        loading={resultLoading}
        streaming={streaming}
        onRetry={handleSubmit}
        historyPath={`/history/${type}`}
      />
    </DivinationCardHeader>
  )
}
