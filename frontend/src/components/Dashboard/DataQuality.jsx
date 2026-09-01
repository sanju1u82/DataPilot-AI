import { Badge, Card, EmptyState, Meter } from "../common/Primitives";
import { scoreTone, severityTone } from "../../utils/format";

/** Quality scores, then the specific problems behind them. */
function DataQuality({ quality }) {
  const tone = scoreTone(quality.overall_score);

  return (
    <div className="dp-stack">
      <Card title="Data quality">
        <div className="dp-score" style={{ marginBottom: 24 }}>
          <div className="dp-score-value" style={{ color: `var(--${tone === "accent" ? "accent-bright" : tone})` }}>
            {quality.overall_score}
            <small>/100</small>
          </div>
          <div>
            <Badge tone={tone}>{quality.grade}</Badge>
            <div className="text-dim" style={{ marginTop: 6, fontSize: 13.5 }}>
              Weighted across completeness, uniqueness, consistency and type integrity.
            </div>
          </div>
        </div>

        {quality.dimensions.map((dimension) => (
          <Meter
            key={dimension.key}
            label={dimension.label}
            value={dimension.score}
            tone={scoreTone(dimension.score)}
            note={dimension.description}
          />
        ))}
      </Card>

      <Card
        title="Issues found"
        actions={
          <div className="dp-row">
            {quality.issue_counts.high > 0 && (
              <Badge tone="danger">{quality.issue_counts.high} high</Badge>
            )}
            {quality.issue_counts.medium > 0 && (
              <Badge tone="warning">{quality.issue_counts.medium} medium</Badge>
            )}
            {quality.issue_counts.low > 0 && (
              <Badge tone="accent">{quality.issue_counts.low} low</Badge>
            )}
          </div>
        }
      >
        {quality.issues.length === 0 ? (
          <EmptyState
            icon="✓"
            title="No quality issues found"
            message="No missing values, duplicate rows or unusable columns were detected."
          />
        ) : (
          quality.issues.map((issue) => (
            <div className="dp-issue" key={issue.type}>
              <div className="dp-issue-head">
                <Badge tone={severityTone(issue.severity)}>{issue.severity}</Badge>
                <span className="dp-issue-title">{issue.title}</span>
              </div>
              <div className="dp-issue-message">{issue.message}</div>
              <div className="dp-issue-fix">→ {issue.recommendation}</div>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}

export default DataQuality;
