export type ClaimStatus = 'unclaimed' | 'active_timer' | 'claimed' | 'expired'

export interface ClaimStatusResponse {
  status: ClaimStatus
  expires_at: string | null
}

export interface StartTimerResponse {
  status: 'active_timer'
  expires_at: string
}
