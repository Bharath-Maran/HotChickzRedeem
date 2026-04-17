import { useState } from 'react'

interface Props {
  onConfirm: () => Promise<void>
  onCancel: () => void
}

export default function ConfirmModal({ onConfirm, onCancel }: Props) {
  const [loading, setLoading] = useState(false)

  const handleConfirm = async () => {
    setLoading(true)
    try {
      await onConfirm()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="modal-overlay"
      onClick={() => {
        if (!loading) onCancel()
      }}
    >
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>🍗 Ready to Claim?</h2>
        <p>
          Confirm that you are currently at the register at
          <br />
          <strong>1716 E Pontiac St, Fort Wayne, IN</strong>.
          <br />
          <br />
          Once confirmed, your FREE Chicken Slider will be marked as
          redeemed and <strong>cannot be used again</strong>.
        </p>

        <div className="modal-actions">
          <button
            className="btn btn-success"
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? 'Redeeming…' : "✅ Yes, I'm at the Register"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
