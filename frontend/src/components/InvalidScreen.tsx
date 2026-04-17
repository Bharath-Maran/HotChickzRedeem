export default function InvalidScreen() {
  return (
    <div className="screen">
      <div className="brand-header">
        <div className="brand-name">🔥 Hot Chickz</div>
        <div className="brand-tagline">Fort Wayne, Indiana</div>
      </div>

      <div className="status-icon" style={{ marginTop: 24 }}>⚠️</div>

      <div className="card">
        <h2 style={{ color: '#ffcf9e' }}>Invalid Link</h2>
        <div className="divider" />
        <p>
          This link is invalid or incomplete. Please check the SMS you received
          from Hot Chickz and try again.
        </p>
      </div>

      <div className="location-chip">
        📍 1716 E Pontiac St, Fort Wayne, IN 46803716 E Pontiac St, Fort Wayne, IN 46803
      </div>
    </div>
  )
}
