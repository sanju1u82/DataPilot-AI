/**
 * Small presentational primitives shared across the dashboard.
 *
 * They exist so that a card, badge or meter looks identical everywhere and a
 * change to one of them lands in every panel at once.
 */

export function Card({ title, actions, children, flush = false }) {
  return (
    <section className="dp-card">
      {(title || actions) && (
        <header className="dp-card-header">
          <h3>{title}</h3>
          {actions}
        </header>
      )}
      <div className={`dp-card-body${flush ? " is-flush" : ""}`}>{children}</div>
    </section>
  );
}

export function Badge({ children, tone = "" }) {
  return <span className={`dp-badge${tone ? ` tone-${tone}` : ""}`}>{children}</span>;
}

export function StatCard({ label, value, hint, tone = "" }) {
  return (
    <div className={`dp-stat${tone ? ` tone-${tone}` : ""}`}>
      <div className="dp-stat-label">{label}</div>
      <div className="dp-stat-value">{value}</div>
      {hint && <div className="dp-stat-hint">{hint}</div>}
    </div>
  );
}

export function Meter({ label, value, tone = "accent", note, display }) {
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="dp-meter">
      <div className="dp-meter-head">
        <span className="dp-meter-name">{label}</span>
        <span className="dp-meter-value">{display ?? `${clamped.toFixed(1)}%`}</span>
      </div>
      <div className="dp-meter-track">
        <div className={`dp-meter-fill tone-${tone}`} style={{ width: `${clamped}%` }} />
      </div>
      {note && <div className="dp-meter-note">{note}</div>}
    </div>
  );
}

export function Loading({ title = "Loading…", message }) {
  return (
    <div className="dp-state">
      <div className="dp-spinner" />
      <div className="dp-state-title">{title}</div>
      {message && <p className="dp-state-message">{message}</p>}
    </div>
  );
}

export function EmptyState({ icon = "○", title, message, action }) {
  return (
    <div className="dp-state">
      <div className="dp-state-icon">{icon}</div>
      <div className="dp-state-title">{title}</div>
      {message && <p className="dp-state-message">{message}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ title = "Something went wrong", message, action }) {
  return (
    <div className="dp-state">
      <div className="dp-state-icon tone-danger">!</div>
      <div className="dp-state-title">{title}</div>
      {message && <p className="dp-state-message">{message}</p>}
      {action}
    </div>
  );
}
