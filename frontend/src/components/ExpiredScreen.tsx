export default function ExpiredScreen() {
  return (
    <div className="screen">
      <div className="brand-header">
        <h1>🔥 Hot Chickz</h1>
      </div>

      <div className="status-icon" style={{ marginTop: 32 }}>
        ⏰
      </div>

      <div className="expired-box">
        <h2>Offer Expired</h2>
        <p>
          Your 7‑day window to claim this FREE Chicken Slider has passed. This
          offer is no longer valid.
        </p>
      </div>

      <div className="card">
        <p>
          Follow Hot Chickz on social media or keep an eye on your messages for
          future deals and promotions!
        </p>
        <p style={{ marginTop: 12, fontSize: '0.82rem', opacity: 0.7 }}>
          📍 1716 E Pontiac St, Fort Wayne, IN
        </p>
      </div>
    </div>
  )
}
