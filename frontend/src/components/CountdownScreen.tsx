import { useState, useEffect } from 'react'
import ConfirmModal from './ConfirmModal'

interface Props {
  expiresAt: string
  onRedeem: () => Promise<void>
}

interface TimeLeft {
  total: number
  days: number
  hours: number
  minutes: number
  seconds: number
}

function calcTimeLeft(expiresAt: string): TimeLeft {
  const diff = new Date(expiresAt).getTime() - Date.now()
  if (diff <= 0) return { total: 0, days: 0, hours: 0, minutes: 0, seconds: 0 }
  return {
    total: diff,
    days: Math.floor(diff / (1000 * 60 * 60 * 24)),
    hours: Math.floor((diff / (1000 * 60 * 60)) % 24),
    minutes: Math.floor((diff / (1000 * 60)) % 60),
    seconds: Math.floor((diff / 1000) % 60),
  }
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

export default function CountdownScreen({ expiresAt, onRedeem }: Props) {
  const [timeLeft, setTimeLeft] = useState<TimeLeft>(calcTimeLeft(expiresAt))
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft(calcTimeLeft(expiresAt))
    }, 1000)
    return () => clearInterval(interval)
  }, [expiresAt])

  return (
    <div className="screen">
      <div className="brand-header">
        <h1>🔥 Hot Chickz</h1>
        <p>Your Offer is Active</p>
      </div>

      <div className="countdown-card">
        <h2>Offer expires in</h2>
        <div className="timer">
          <div className="time-unit">
            <span className="time-value">{pad(timeLeft.days)}</span>
            <span className="time-label">Days</span>
          </div>
          <span className="time-colon">:</span>
          <div className="time-unit">
            <span className="time-value">{pad(timeLeft.hours)}</span>
            <span className="time-label">Hrs</span>
          </div>
          <span className="time-colon">:</span>
          <div className="time-unit">
            <span className="time-value">{pad(timeLeft.minutes)}</span>
            <span className="time-label">Min</span>
          </div>
          <span className="time-colon">:</span>
          <div className="time-unit">
            <span className="time-value">{pad(timeLeft.seconds)}</span>
            <span className="time-label">Sec</span>
          </div>
        </div>
      </div>

      <div className="card">
        <p>🍗 <strong>1× FREE Chicken Slider</strong></p>
        <div className="divider" />
        <p style={{ fontSize: '0.85rem' }}>
          When you're at the register, tap the button below to complete your
          redemption. This action cannot be undone.
        </p>
      </div>

      <div className="offer-details">
        <p>📍 1716 E Pontiac St, Fort Wayne, IN</p>
        <p>🔒 One-time use only</p>
      </div>

      <button className="btn btn-primary" onClick={() => setShowModal(true)}>
        ✅ I'm at the Register — Redeem Now
      </button>

      {showModal && (
        <ConfirmModal
          onConfirm={onRedeem}
          onCancel={() => setShowModal(false)}
        />
      )}
    </div>
  )
}
