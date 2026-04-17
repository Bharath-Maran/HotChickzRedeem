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
        <div className="brand-name">🔥 Hot Chickz</div>
        <div className="brand-tagline">Fort Wayne, Indiana</div>
      </div>

      <div className="steps">
        <div className="step">
          <div className="step-dot active">1</div>
          <div className="step-label active">Claim</div>
        </div>
        <div className="step-line" />
        <div className="step">
          <div className="step-dot">2</div>
          <div className="step-label">Visit</div>
        </div>
        <div className="step-line" />
        <div className="step">
          <div className="step-dot">3</div>
          <div className="step-label">Enjoy</div>
        </div>
      </div>

      <div className="offer-badge">🍗</div>

      <div className="voucher">
        <div className="voucher-header">
          <span className="free-label">— One Complimentary —</span>
          <span className="item-name">Chicken Slider</span>
        </div>
        <div className="voucher-tear">
          <div className="voucher-dots">
            {Array.from({ length: 16 }).map((_, i) => <span key={i} />)}
          </div>
        </div>
        <div className="voucher-body">
          <p>
            Tap <strong style={{ color: '#fff' }}>Claim Now</strong> to start your 7-day window.
            Then bring this screen to the register to redeem your free slider.
          </p>
        </div>
      </div>

      <div className="location-chip">
        📍 1716 E Pontiac St, Fort Wayne, IN 46803
      </div>

      <button className="btn btn-primary" onClick={handleClick} disabled={loading}>
        {loading ? 'Starting your offer…' : '🔥 Claim Now'}
      </button>

      <p className="fine-print">
        Valid for one-time use only · One per customer · Dine-in only<br />
        Cannot be combined with other offers · Expires 7 days after claiming
      </plassName="voucher-header">
          <span className="free-label">— One Complimentary —</span>
          <span className="item-name">Chicken Slider</span>
        </div>
        <div className="voucher-tear">
          <div className="voucher-dots">
            {Array.from({ length: 16 }).map((_, i) => <span key={i} />)}
          </div>
        </div>
        <div className="voucher-body">
          <p>
            Tap <strong style={{ color: '#fff' }}>Claim Now</strong> to start your 7-day window.
            Then bring this screen to the register to redeem your free slider.
          </p>
        </div>
      </div>

      <div className="location-chip">
        📍 1716 E Pontiac St, Fort Wayne, IN 46803
      </div>

      <button className="btn btn-primary" onClick={handleClick} disabled={loading}>
        {loading ? 'Starting your offer…' : '🔥 Claim Now'}
      </button>

      <p className="fine-print">
        Valid for one-time use only · One per customer · Dine-in only<br />
        Cannot be combined with other offers · Expires 7 days after claiming
      </p>
    </div>
  )
}
