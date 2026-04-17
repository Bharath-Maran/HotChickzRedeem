export default function ClaimedScreen() {
  const now = new Date()
  const dateStr = now.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
  const timeStr = now.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className="screen">
      <div className="brand-header">
        <h1>🔥 Hot Chickz</h1>
        <p>Redemption Complete</p>
      </div>

      <div className="status-icon">✅</div>

      <div className="receipt-box">
        <h2>Offer Claimed!</h2>
        <p style={{ color: '#ffd4a0', marginBottom: 18, fontSize: '0.9rem' }}>
          Your FREE Chicken Slider has been successfully redeemed.
        </p>

        <div className="divider" />

        <div style={{ marginTop: 14 }}>
          <div className="receipt-row">
            <span>Item</span>
            <span>FREE Chicken Slider ×1</span>
          </div>
          <div className="receipt-row">
            <span>Value</span>
            <span>Complimentary</span>
          </div>
          <div className="receipt-row">
            <span>Date</span>
            <span>{dateStr}</span>
          </div>
          <div className="receipt-row">
            <span>Time</span>
            <span>{timeStr}</span>
          </div>
          <div className="receipt-row">
            <span>Location</span>
            <span>1716 E Pontiac St, Fort Wayne, IN</span>
          </div>
        </div>
      </div>

      <div className="card">
        <p>🙏 Thank you for visiting Hot Chickz! We hope you love your slider.</p>
      </div>
    </div>
  )
}
