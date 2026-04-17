import { useState, useEffect } from 'react'
import type { ClaimStatus, ClaimStatusResponse, StartTimerResponse } from './types'
import LoadingScreen from './components/LoadingScreen'
import InvalidScreen from './components/InvalidScreen'
import UnclaimedScreen from './components/UnclaimedScreen'
import CountdownScreen from './components/CountdownScreen'
import ClaimedScreen from './components/ClaimedScreen'
import ExpiredScreen from './components/ExpiredScreen'

// VITE_API_URL is empty in development (Vite proxy handles /api → localhost:8000)
// Set it to the deployed backend URL in production (e.g. https://hotchickz-api.onrender.com)
const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? ''

export default function App() {
  const [status, setStatus] = useState<ClaimStatus | null>(null)
  const [expiresAt, setExpiresAt] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)

  // Read the ?code= query parameter from the SMS link
  const code = new URLSearchParams(window.location.search).get('code')

  useEffect(() => {
    if (!code) {
      setLoading(false)
      return
    }

    fetch(`${API_BASE}/api/claim-status?code=${encodeURIComponent(code)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Server error: ${res.status}`)
        return res.json() as Promise<ClaimStatusResponse>
      })
      .then((data) => {
        setStatus(data.status)
        setExpiresAt(data.expires_at)
        setLoading(false)
      })
      .catch((err: unknown) => {
        setFetchError((err as Error).message ?? 'Unknown error')
        setLoading(false)
      })
  }, [code])

  // Called when the user taps "Claim Now" on the UnclaimedScreen
  const handleClaimNow = async () => {
    if (!code) return
    const res = await fetch(`${API_BASE}/api/start-timer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contact_id: code }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({})) as { detail?: string }
      throw new Error(body.detail ?? 'Failed to start timer')
    }
    const data = (await res.json()) as StartTimerResponse
    setStatus('active_timer')
    setExpiresAt(data.expires_at)
  }

  // Called after the user confirms at the register in the modal
  const handleRedeem = async () => {
    if (!code) return
    const res = await fetch(`${API_BASE}/api/redeem`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contact_id: code }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({})) as { detail?: string }
      throw new Error(body.detail ?? 'Failed to redeem')
    }
    setStatus('claimed')
  }

  if (loading) return <LoadingScreen />
  if (!code) return <InvalidScreen />

  if (fetchError) {
    return (
      <div className="screen" style={{ justifyContent: 'center', textAlign: 'center' }}>
        <p style={{ color: '#ffd4a0' }}>
          Could not load your offer. Please check your connection and try again.
        </p>
        <p style={{ color: 'rgba(255,212,160,0.5)', fontSize: '0.8rem', marginTop: 8 }}>
          {fetchError}
        </p>
      </div>
    )
  }

  switch (status) {
    case 'unclaimed':
      return <UnclaimedScreen onClaimNow={handleClaimNow} />
    case 'active_timer':
      return <CountdownScreen expiresAt={expiresAt!} onRedeem={handleRedeem} />
    case 'claimed':
      return <ClaimedScreen />
    case 'expired':
      return <ExpiredScreen />
    default:
      return <InvalidScreen />
  }
}
