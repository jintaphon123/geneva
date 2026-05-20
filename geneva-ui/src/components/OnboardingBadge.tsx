import { useEffect, useState } from "react"
import { X } from "lucide-react"

type OnboardingBadgeProps = {
  onStart: () => void
}

export function OnboardingBadge({ onStart }: OnboardingBadgeProps) {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    let isCancelled = false

    const checkOnboardingStatus = async () => {
      try {
        const response = await fetch("/api/onboarding/status")
        if (!response.ok) throw new Error("Unable to load onboarding status")

        const data = (await response.json()) as {
          needs_onboarding?: boolean
          complete?: boolean
        }

        const needsOnboarding = Boolean(data?.needs_onboarding)
        const complete = Boolean(data?.complete)
        if (!isCancelled && (!needsOnboarding || complete)) {
          setIsVisible(false)
        }
      } catch {
        if (!isCancelled) {
          setIsVisible(false)
        }
      }
    }

    void checkOnboardingStatus()

    return () => {
      isCancelled = true
    }
  }, [])

  if (!isVisible) return null

  return (
    <div className="onboarding-badge">
      <div>
        <div>
          <p>
            Geneva ยังไม่รู้จักคุณ — ตั้งค่า Second Brain ของคุณ
          </p>
          <button
            onClick={onStart}
            type="button"
          >
            เริ่มต้น
          </button>
          <button
            aria-label="ปิดการแจ้งเตือน"
            onClick={() => setIsVisible(false)}
            type="button"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
