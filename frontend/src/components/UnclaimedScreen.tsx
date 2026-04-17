import { useState } from 'react'

interface Props {
  onClaimNow: () => Promise<void>
}

export default function UnclaimedScreen({ onClaimNow }: Props) {
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    setLoading(true)
    try {
      await onClaimNow()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="screen">
      <div className="brand-header">
        <h1>🔥 Hot Chickz</h1>
        <p>Special Offer — Fort Wayne</p>
      </div>

      <div className="offer-badge">🍗</div>

      <div className="card">
        <h2>You've got a FREE Chicken Slider!</h2>
        <div className="divider" />
        <p>
          Tap <strong>Claim Now</strong> to start your 7‑day window. Then
          bring this screen to the register at 1716&nbsp;E Pontiac&nbsp;St to
          redeem it.
        </p>
      </div>

      <div className="offer-details">
        <p>📍 1716 E Pontiac St, Fort Wayne, IN</p>
        <p>⏰ Valid for 7 days after claiming</p>
        <p>🔒 One-time use only — cannot be reused</p>
      </div>

      <button className="btn btn-primary" onClick={handleClick} disabled={loading}>
        {loading ? 'Starting your offer…' : '🔥 Claim Now'}
      </button>
    </div>
  )
}
