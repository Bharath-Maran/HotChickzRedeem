export default function ExpiredScreen() {
  return (
    <div className="screen">
      <div className="brand-header">
        <div className="brand-name">🔥 Hot Chickz</div>
        <div className="brand-tagline">Fort Wayne, Indiana</div>
      </div>

      <div className="status-icon" style={{ marginTop: 24 }}>⏰</div>

      <div className="expired-box">
        <h2>Offer Expired</h2>
        <p>
          Your 7-day window to claim this FREE Chicken Slider has passed.
          This offer is no longer valid.
        </p>
      </div>

      <div className="card">
        <p>
          Follow Hot Chickz on social media or keep an eye on your messages
          for future deals and promotions!
        </p>
      </div>

      <div className="location-chip">
        📍 1716 E Pontiac St, Fort Wayne, IN 46803716 E Pontiac St, Fort Wayne, IN 46803
      </div>
    </div>
  )
}
