import { useEffect, useState } from "react";
import { Badge, Card } from "../common/Primitives";
import { fetchPredictionSchema, predict } from "../../services/api";
import { formatDecimal, formatPercent } from "../../utils/format";

/**
 * Try the trained model on a single hand-entered row.
 *
 * Blank fields are sent as null rather than empty strings, so the pipeline's
 * imputer fills them the same way it did during training.
 */
function Predictions({ runId }) {
  const [schema, setSchema] = useState(null);
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setSchema(null);
    setResult(null);
    setValues({});

    fetchPredictionSchema(runId)
      .then((data) => !cancelled && setSchema(data.schema))
      .catch((err) => !cancelled && setError(err.message));

    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (error) {
    return (
      <Card title="Try a prediction">
        <p className="text-dim">{error}</p>
      </Card>
    );
  }

  if (!schema) {
    return (
      <Card title="Try a prediction">
        <p className="text-faint">Loading the model's input fields…</p>
      </Card>
    );
  }

  const fields = [
    ...schema.numeric.map((name) => ({ name, kind: "number" })),
    ...schema.datetime.map((name) => ({ name, kind: "date" })),
    ...schema.categorical.map((name) => ({ name, kind: "text" })),
  ];

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const row = {};
      for (const field of fields) {
        const raw = values[field.name];
        if (raw === undefined || raw === "") {
          row[field.name] = null;
        } else if (field.kind === "number") {
          const parsed = Number(raw);
          row[field.name] = Number.isNaN(parsed) ? null : parsed;
        } else {
          row[field.name] = raw;
        }
      }

      const data = await predict(runId, [row]);
      setResult(data.predictions[0] ?? null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      title="Try a prediction"
      actions={<Badge tone="accent">{schema.model}</Badge>}
    >
      <p className="text-dim" style={{ marginTop: 0, fontSize: 13.5 }}>
        Enter values to predict <strong>{schema.target}</strong>. Leave a field
        blank and the model imputes it exactly as it did during training.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: 14,
          marginTop: 18,
        }}
      >
        {fields.map((field) => (
          <div key={field.name}>
            <label className="dp-field-label" htmlFor={`predict-${field.name}`}>
              {field.name}
            </label>
            <input
              id={`predict-${field.name}`}
              className="dp-input"
              type={field.kind === "number" ? "number" : "text"}
              step={field.kind === "number" ? "any" : undefined}
              placeholder={field.kind === "date" ? "YYYY-MM-DD" : ""}
              value={values[field.name] ?? ""}
              onChange={(event) =>
                setValues({ ...values, [field.name]: event.target.value })
              }
            />
          </div>
        ))}
      </div>

      {fields.length === 0 && (
        <p className="text-faint">This model takes no input columns.</p>
      )}

      <button
        type="button"
        className="dp-btn dp-btn-primary"
        style={{ marginTop: 18 }}
        disabled={busy || fields.length === 0}
        onClick={submit}
      >
        {busy ? "Predicting…" : "Predict"}
      </button>

      {result && (
        <div className="dp-headline" style={{ marginTop: 20 }}>
          <div className="eyebrow">Predicted {schema.target}</div>
          <div style={{ fontSize: 26, fontWeight: 700, marginTop: 4 }}>
            {typeof result.prediction === "number"
              ? formatDecimal(result.prediction, 4)
              : String(result.prediction)}
          </div>
          {result.confidence !== undefined && result.confidence !== null && (
            <div className="text-dim" style={{ fontSize: 13.5, marginTop: 4 }}>
              Confidence {formatPercent(result.confidence * 100, 1)}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export default Predictions;
