import { useCallback, useEffect, useRef, useState } from "react";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  Meter,
} from "../common/Primitives";
import Predictions from "./Predictions";
import {
  fetchRun,
  fetchTargetSuggestions,
  startTraining,
} from "../../services/api";
import { formatDecimal, formatNumber, formatPercent } from "../../utils/format";

const POLL_INTERVAL_MS = 1500;

const METRIC_LABELS = {
  accuracy: "Accuracy",
  precision: "Precision",
  recall: "Recall",
  f1: "F1",
  roc_auc: "ROC AUC",
  r2: "R²",
  mae: "MAE",
  rmse: "RMSE",
  mse: "MSE",
  mape: "MAPE (%)",
};

const PROBLEM_LABELS = {
  binary_classification: "Binary classification",
  multiclass_classification: "Multiclass classification",
  regression: "Regression",
};

function MetricGrid({ metrics }) {
  const entries = Object.entries(metrics).filter(
    ([key, value]) =>
      METRIC_LABELS[key] && value !== null && value !== undefined
  );

  return (
    <div className="dp-stat-grid">
      {entries.map(([key, value]) => (
        <div className="dp-stat tone-cyan" key={key}>
          <div className="dp-stat-label">{METRIC_LABELS[key]}</div>
          <div className="dp-stat-value">{formatDecimal(value, 4)}</div>
        </div>
      ))}
    </div>
  );
}

function ConfusionMatrix({ labels, matrix }) {
  return (
    <div className="dp-table-scroll">
      <table className="dp-matrix">
        <thead>
          <tr>
            <th />
            {labels.map((label) => (
              <th key={label}>predicted {label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, rowIndex) => (
            <tr key={labels[rowIndex]}>
              <th>actual {labels[rowIndex]}</th>
              {row.map((count, columnIndex) => (
                <td
                  key={columnIndex}
                  className={rowIndex === columnIndex ? "is-diagonal" : undefined}
                >
                  {formatNumber(count)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Leaderboard({ result }) {
  const metricKey = result.primary_metric.key;

  return (
    <Card
      title="Model leaderboard"
      actions={<Badge tone="accent">ranked by {result.primary_metric.label}</Badge>}
    >
      {result.leaderboard.map((model) => (
        <div
          className={`dp-leader${model.is_best ? " is-best" : ""}${
            model.status !== "success" ? " is-failed" : ""
          }`}
          key={model.key}
        >
          <div className="dp-leader-rank">
            {model.status === "success" ? model.rank : "—"}
          </div>
          <div className="dp-leader-body">
            <div className="dp-leader-name">
              {model.name}{" "}
              {model.is_best && <Badge tone="success">best</Badge>}
              {model.status !== "success" && <Badge tone="danger">failed</Badge>}
            </div>
            <div className="dp-leader-desc">
              {model.status === "success"
                ? `${model.description} · trained in ${model.training_seconds}s`
                : model.error}
            </div>
          </div>
          {model.status === "success" && (
            <div className="dp-leader-score">
              <div className="dp-leader-score-value">
                {formatDecimal(model.metrics[metricKey], 4)}
              </div>
              <div className="dp-leader-score-label">
                {result.primary_metric.label}
              </div>
            </div>
          )}
        </div>
      ))}
    </Card>
  );
}

function FeatureImportance({ importance }) {
  if (!importance.length) {
    return null;
  }
  const peak = Math.max(...importance.map((item) => item.value), 0.0001);

  return (
    <Card title="What drove the predictions">
      <p className="text-dim" style={{ marginTop: 0, fontSize: 13.5 }}>
        Relative influence of each feature on the winning model
        {importance[0]?.kind ? ` (${importance[0].kind})` : ""}.
      </p>
      {importance.map((item) => (
        <div className="dp-bar-row" key={item.feature}>
          <div className="dp-bar-head">
            <span className="dp-bar-label" title={item.feature}>
              {item.feature}
            </span>
            <span className="dp-bar-count">{formatPercent(item.percentage, 1)}</span>
          </div>
          <div className="dp-bar-track">
            <div
              className="dp-bar-fill"
              style={{ width: `${Math.max((item.value / peak) * 100, 1)}%` }}
            />
          </div>
        </div>
      ))}
    </Card>
  );
}

function Pipeline({ result }) {
  return (
    <div className="dp-grid-2">
      <Card title="Preprocessing applied">
        <div className="dp-insight-list">
          {result.preprocessing.map((step) => (
            <div className="dp-insight tone-neutral" key={step.step}>
              <span className="dp-insight-dot" aria-hidden="true" />
              <span>
                <strong>{step.step}</strong>
                <div className="text-dim" style={{ fontSize: 13 }}>
                  {step.detail}
                </div>
              </span>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Features used">
        <div className="dp-row" style={{ marginBottom: 14 }}>
          <Badge tone="cyan">{result.features.numeric.length} numeric</Badge>
          <Badge tone="accent">{result.features.categorical.length} categorical</Badge>
          <Badge>{result.training.encoded_feature_count} after encoding</Badge>
        </div>

        <div className="text-dim" style={{ fontSize: 13.5, marginBottom: 10 }}>
          Trained on {formatNumber(result.training.train_rows)} rows, evaluated on{" "}
          {formatNumber(result.training.test_rows)} held out.
          {result.training.sampled_from &&
            ` Sampled from ${formatNumber(result.training.sampled_from)} total rows.`}
        </div>

        {result.features.dropped.length > 0 && (
          <>
            <div className="eyebrow" style={{ marginBottom: 8 }}>
              Excluded columns
            </div>
            {result.features.dropped.map((item) => (
              <div key={item.column} style={{ fontSize: 13, marginBottom: 4 }}>
                <span style={{ fontWeight: 600 }}>{item.column}</span>{" "}
                <span className="text-faint">— {item.reason}</span>
              </div>
            ))}
          </>
        )}
      </Card>
    </div>
  );
}

function AutoML({ datasetId }) {
  const [targets, setTargets] = useState([]);
  const [targetsLoaded, setTargetsLoaded] = useState(false);
  const [target, setTarget] = useState("");
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);
  const [starting, setStarting] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    fetchTargetSuggestions(datasetId)
      .then((data) => {
        if (cancelled) return;
        setTargets(data.targets);
        setTargetsLoaded(true);
        setTarget((current) => current || data.targets[0]?.column || "");
      })
      .catch((err) => {
        if (cancelled) return;
        setTargetsLoaded(true);
        setError(err.message);
      });

    return () => {
      cancelled = true;
    };
  }, [datasetId]);

  // Stop polling when the component unmounts mid-run.
  useEffect(() => () => clearTimeout(pollRef.current), []);

  const poll = useCallback((runId) => {
    fetchRun(runId)
      .then((data) => {
        setRun(data.run);
        if (data.run.status === "queued" || data.run.status === "running") {
          pollRef.current = setTimeout(() => poll(runId), POLL_INTERVAL_MS);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  const train = async () => {
    setError(null);
    setRun(null);
    setStarting(true);
    try {
      const data = await startTraining(datasetId, target);
      setRun(data.run);
      poll(data.run.run_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setStarting(false);
    }
  };

  const busy = starting || run?.status === "queued" || run?.status === "running";
  const result = run?.status === "completed" ? run.result : null;

  return (
    <div className="dp-stack">
      <Card title="Train a model">
        <p className="text-dim" style={{ marginTop: 0 }}>
          Pick the column you want to predict. DataPilot detects the problem type,
          preprocesses the data, trains several models and picks the best one.
        </p>

        <div className="dp-grid-2" style={{ alignItems: "end" }}>
          <div>
            <label className="dp-field-label" htmlFor="automl-target">
              Target column
            </label>
            <select
              id="automl-target"
              className="dp-select"
              value={target}
              disabled={busy || !targets.length}
              onChange={(event) => setTarget(event.target.value)}
            >
              {targets.map((suggestion) => (
                <option key={suggestion.column} value={suggestion.column}>
                  {suggestion.column} — {suggestion.suggested_problem} (
                  {suggestion.unique_values} distinct)
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="dp-btn dp-btn-primary"
            disabled={!target || busy}
            onClick={train}
          >
            {busy ? "Training…" : "Run AutoML"}
          </button>
        </div>

        {!targetsLoaded && !error && (
          <p className="text-faint" style={{ marginTop: 14, fontSize: 13.5 }}>
            Looking for suitable target columns…
          </p>
        )}

        {targetsLoaded && targets.length === 0 && !error && (
          <p className="text-faint" style={{ marginTop: 14, fontSize: 13.5 }}>
            No column in this dataset is suitable as a prediction target. Every
            column is either constant, an identifier, free text, or mostly empty.
          </p>
        )}
      </Card>

      {busy && run && (
        <Card title="Training in progress">
          <Meter
            label={run.stage}
            value={run.progress}
            tone="accent"
            display={`${run.progress}%`}
          />
        </Card>
      )}

      {error && <ErrorState title="Training couldn't start" message={error} />}

      {run?.status === "failed" && (
        <ErrorState title="Training failed" message={run.error} />
      )}

      {result && (
        <>
          <Card
            title="Best model"
            actions={
              <Badge tone="accent">
                {PROBLEM_LABELS[result.problem.problem_type]}
              </Badge>
            }
          >
            <div className="dp-row" style={{ justifyContent: "space-between" }}>
              <div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>
                  {result.best_model.name}
                </div>
                <div className="text-dim" style={{ fontSize: 13.5 }}>
                  Predicting <strong>{result.problem.target}</strong> ·{" "}
                  {result.best_model.description}
                </div>
              </div>
              <div className="dp-leader-score">
                <div className="dp-leader-score-value">
                  {formatDecimal(result.best_model.score, 4)}
                </div>
                <div className="dp-leader-score-label">
                  {result.primary_metric.label}
                </div>
              </div>
            </div>

            <div style={{ marginTop: 20 }}>
              <MetricGrid metrics={result.best_model.metrics} />
            </div>
          </Card>

          {result.best_model.metrics.confusion_matrix && (
            <Card title="Confusion matrix">
              <ConfusionMatrix
                labels={result.best_model.metrics.labels}
                matrix={result.best_model.metrics.confusion_matrix}
              />
            </Card>
          )}

          <Leaderboard result={result} />
          <FeatureImportance importance={result.feature_importance} />
          <Pipeline result={result} />
          <Predictions runId={run.run_id} />
        </>
      )}

      {!run && !error && targets.length > 0 && (
        <EmptyState
          title="No model trained yet"
          message="Choose a target column above and run AutoML to compare models."
        />
      )}
    </div>
  );
}

export default AutoML;
