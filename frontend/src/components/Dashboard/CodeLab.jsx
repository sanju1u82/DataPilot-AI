import { useEffect, useState } from "react";
import { Badge, Card } from "../common/Primitives";
import { fetchGeneratedCode } from "../../services/api";

/**
 * The analysis as a runnable Python script.
 *
 * Lets a user take DataPilot's work into their own notebook instead of being
 * locked into the UI.
 */
function CodeLab({ datasetId, profile }) {
  const [target, setTarget] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const modellable = profile.columns.filter(
    (column) => !column.is_constant && !column.is_empty && !column.is_identifier
  );

  useEffect(() => {
    let cancelled = false;
    fetchGeneratedCode(datasetId, target || undefined)
      .then((data) => !cancelled && setCode(data.code))
      .catch((err) => !cancelled && setError(err.message));

    return () => {
      cancelled = true;
    };
  }, [datasetId, target]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access is blocked outside a secure context; the code is
      // still on screen to select manually.
      setCopied(false);
    }
  };

  return (
    <div className="dp-stack">
      <Card title="Generate analysis code">
        <p className="text-dim" style={{ marginTop: 0 }}>
          A standalone pandas and scikit-learn script for this dataset. Optionally
          pick a target column to include a full model pipeline.
        </p>

        <label className="dp-field-label" htmlFor="code-target">
          Include a model for (optional)
        </label>
        <select
          id="code-target"
          className="dp-select"
          value={target}
          onChange={(event) => setTarget(event.target.value)}
        >
          <option value="">Profiling only — no model</option>
          {modellable.map((column) => (
            <option key={column.name} value={column.name}>
              {column.name}
            </option>
          ))}
        </select>
      </Card>

      <Card
        title="dataPilot_analysis.py"
        flush
        actions={
          <div className="dp-row">
            {copied && <Badge tone="success">copied</Badge>}
            <button type="button" className="dp-btn dp-btn-ghost" onClick={copy}>
              Copy
            </button>
          </div>
        }
      >
        {error ? (
          <p className="text-dim" style={{ padding: 20 }}>
            {error}
          </p>
        ) : (
          <pre className="dp-code">{code || "Generating…"}</pre>
        )}
      </Card>
    </div>
  );
}

export default CodeLab;
