import type { OnboardingStatus } from "@/types"

import { jsonFetch } from "./core"

export async function fetchOnboardingStatus(): Promise<OnboardingStatus> {
  return jsonFetch<OnboardingStatus>("/api/onboarding/status")
}
