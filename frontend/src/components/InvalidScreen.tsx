export default function InvalidScreen() {
  return (
    <div className="screen">
      <div className="brand-header">
        <h1>🔥 Hot Chickz</h1>
      </div>

      <div className="status-icon" style={{ marginTop: 32 }}>
        ⚠️
      </div>

      <div className="card">
        <h2 style={{ color: '#ffd4a0' }}>Invalid Link</h2>
        <div className="divider" />
        <p>
          This link is invalid or incomplete. Please check the SMS you received
          from Hot Chickz and try again.
        </p>
        <p style={{ marginTop: 12, fontSize: '0.8rem', opacity: 0.7 }}>
          📍 1716 E Pontiac St, Fort Wayne, IN
        </p>
      </div>
    </div>
  )
}
