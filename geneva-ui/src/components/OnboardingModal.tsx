import { type FormEvent, useEffect, useMemo, useRef, useState } from "react"
import { Loader2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { streamChat } from "@/lib/api/stream-api"

type OnboardingModalProps = {
  open: boolean
  onClose: () => void
  onComplete: () => void
}

type Message = {
  id: string
  role: "assistant" | "user"
  content: string
}

export function OnboardingModal({ open, onClose, onComplete }: OnboardingModalProps) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isStarting, setIsStarting] = useState(false)
  const [isResponding, setIsResponding] = useState(false)
  const [error, setError] = useState("")
  const scrollAnchorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) {
      setSessionId(null)
      setMessages([])
      setInput("")
      setIsStarting(false)
      setIsResponding(false)
      setError("")
      return
    }

    let cancelled = false

    const startOnboarding = async () => {
      setIsStarting(true)
      setSessionId(null)
      setMessages([])
      setInput("")
      setError("")

      try {
        const response = await fetch("/api/onboarding/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        })

        if (!response.ok) {
          throw new Error("Failed to start onboarding")
        }

        const data = (await response.json()) as {
          session_id?: string | null
          first_message?: string
        }

        if (cancelled) return
        setSessionId(data.session_id ?? null)
        setMessages([
          {
            id: `ai-${cryptoRandomId()}`,
            role: "assistant",
            content: data.first_message ?? "",
          },
        ])
      } catch {
        if (!cancelled) {
          setError("ไม่สามารถเริ่ม onboarding ได้ กรุณาปิดแล้วลองใหม่อีกครั้ง")
          setSessionId(null)
          setMessages([])
        }
      } finally {
        if (!cancelled) setIsStarting(false)
      }
    }

    void startOnboarding()

    return () => {
      cancelled = true
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const timer = window.setTimeout(() => {
      scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" })
    }, 0)
    return () => window.clearTimeout(timer)
  }, [messages, open, isResponding, isStarting])

  const canSend = useMemo(() => {
    const hasText = input.trim().length > 0
    return open && Boolean(sessionId) && !isStarting && !isResponding && hasText
  }, [input, sessionId, open, isStarting, isResponding])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const messageText = input.trim()
    if (!canSend || !sessionId) return

    const userMessage: Message = {
      id: `user-${cryptoRandomId()}`,
      role: "user",
      content: messageText,
    }
    const assistantMessageId = `ai-${cryptoRandomId()}`

    setMessages((prev) => [...prev, userMessage, { id: assistantMessageId, role: "assistant", content: "" }])
    setInput("")
    setIsResponding(true)
    setError("")

    try {
      await streamChat({
        message: messageText,
        sessionId,
        onText: (chunk) => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantMessageId
                ? { ...message, content: `${message.content}${chunk}` }
                : message,
            ),
          )
        },
        onSession: (nextSessionId) => {
          setSessionId(nextSessionId)
        },
      })
      onComplete()
      onClose()
    } catch {
      setMessages((prev) =>
        prev.map((message) =>
          message.id === assistantMessageId
            ? { ...message, content: "เกิดข้อผิดพลาดขณะดึงคำตอบจาก AI" }
            : message,
        ),
      )
    } finally {
      setIsResponding(false)
    }
  }

  if (!open) return null

  return (
    <div className="onboarding-modal-backdrop">
      <div className="onboarding-modal">
        <header className="onboarding-modal-header">
          <h2>Set up Geneva</h2>
          <Button
            onClick={onClose}
            size="icon"
            variant="quiet"
            type="button"
          >
            <X className="size-4" />
          </Button>
        </header>

        <ScrollArea className="onboarding-modal-scroll">
          <div className="onboarding-message-list">
            {messages.map((message) => {
              const isAssistant = message.role === "assistant"
              return (
                <div
                  key={message.id}
                  className={isAssistant ? "onboarding-message assistant" : "onboarding-message user"}
                >
                  {message.content}
                </div>
              )
            })}

            {isStarting && (
              <div className="onboarding-loading">
                <Loader2 className="size-4 animate-spin" />
                กำลังเริ่มการตั้งค่า...
              </div>
            )}

            {!isStarting && error && <p className="onboarding-error">{error}</p>}
            <div ref={scrollAnchorRef} />
          </div>
        </ScrollArea>

        <form
          className="onboarding-composer"
          onSubmit={handleSubmit}
        >
          <input
            disabled={isStarting || isResponding}
            onChange={(event) => setInput(event.target.value)}
            placeholder="พิมพ์ข้อความของคุณ..."
            type="text"
            value={input}
          />
          <Button
            disabled={!canSend || isResponding}
            size="sm"
            type="submit"
          >
            {isResponding ? <Loader2 className="size-4 animate-spin" /> : "ส่ง"}
          </Button>
        </form>
      </div>
    </div>
  )
}

function cryptoRandomId() {
  return Math.random().toString(36).slice(2, 11)
}
