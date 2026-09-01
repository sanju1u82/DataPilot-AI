import { useEffect, useState } from "react";

const STEPS = [
  "Reading dataset",
  "Detecting data types",
  "Checking data quality",
  "Generating insights",
];

/**
 * Progress list shown while the backend analyses an upload.
 *
 * The backend returns the whole analysis in one response, so these steps are
 * paced on a timer rather than reported per stage. They advance to the
 * second-to-last step and hold there until the real response lands, so the UI
 * never claims to have finished before it has.
 */
function ProcessingSteps({ intervalMs = 550 }) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrent((step) => Math.min(step + 1, STEPS.length - 1));
    }, intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs]);

  return (
    <div className="dp-steps">
      {STEPS.map((step, index) => {
        const done = index < current;
        const active = index === current;
        return (
          <div
            key={step}
            className={`dp-step${done ? " is-done" : ""}${active ? " is-active" : ""}`}
          >
            <span className="dp-step-marker">{done ? "✓" : active ? "•" : "○"}</span>
            {step}
          </div>
        );
      })}
    </div>
  );
}

export default ProcessingSteps;
