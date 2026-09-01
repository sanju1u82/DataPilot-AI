import { Link } from "react-router-dom";
import { Badge } from "../common/Primitives";

/** Top bar. Shows the active dataset once one is loaded. */
function Navbar({ dataset, children }) {
  return (
    <nav className="dp-navbar">
      <Link to="/" className="dp-brand">
        <span className="dp-brand-mark">DP</span>
        DataPilot AI
      </Link>

      <div className="dp-navbar-meta">
        {dataset && (
          <>
            <span className="dp-navbar-file" title={dataset.filename}>
              {dataset.filename}
            </span>
            <Badge tone="accent">
              {dataset.rows.toLocaleString()} × {dataset.columns}
            </Badge>
          </>
        )}
        {children}
      </div>
    </nav>
  );
}

export default Navbar;
